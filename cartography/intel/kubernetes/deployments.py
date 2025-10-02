import json
import logging
from typing import Any

import neo4j
from kubernetes.client.models import V1Deployment

from cartography.client.core.tx import load
from cartography.graph.job import GraphJob
from cartography.intel.kubernetes.util import get_epoch
from cartography.intel.kubernetes.util import k8s_paginate
from cartography.intel.kubernetes.util import K8sClient
from cartography.models.kubernetes.deployments import KubernetesDeploymentSchema
from cartography.util import timeit

logger = logging.getLogger(__name__)


@timeit
def get_deployments(client: K8sClient) -> list[V1Deployment]:
    """
    Get all deployments across all namespaces.
    """
    items = k8s_paginate(client.apps_v1.list_deployment_for_all_namespaces)
    return items


def _format_labels(labels: dict[str, str]) -> str:
    return json.dumps(labels) if labels else "{}"


def _extract_configmaps_and_secrets(dep: V1Deployment) -> tuple[list[str], list[str]]:
    """
    Get ConfigMaps and Secrets that Deployment uses.
    """
    configmaps: set[str] = set()
    secrets: set[str] = set()

    if not dep.spec or not dep.spec.template or not dep.spec.template.spec:
        return list(configmaps), list(secrets)

    spec = dep.spec.template.spec

    if spec.volumes:
        for v in spec.volumes:
            if v.config_map:
                configmaps.add(v.config_map.name)
            if v.secret:
                secrets.add(v.secret.secret_name)

    if spec.containers:
        for c in spec.containers:
            if c.env:
                for e in c.env:
                    if e.value_from:
                        if e.value_from.config_map_key_ref:
                            configmaps.add(e.value_from.config_map_key_ref.name)
                        if e.value_from.secret_key_ref:
                            secrets.add(e.value_from.secret_key_ref.name)
            if c.env_from:
                for ef in c.env_from:
                    if ef.config_map_ref and ef.config_map_ref.name:
                        configmaps.add(ef.config_map_ref.name)
                    if ef.secret_ref and ef.secret_ref.name:
                        secrets.add(ef.secret_ref.name)

    return list(configmaps), list(secrets)


def transform_deployments(deployments: list[V1Deployment]) -> list[dict[str, Any]]:
    """
    Transform K8s Deployment objects into dictionaries for Neo4j.
    """
    transformed = []
    for dep in deployments:
        configmaps, secrets = _extract_configmaps_and_secrets(dep)
        transformed.append(
            {
                "uid": dep.metadata.uid,
                "name": dep.metadata.name,
                "creation_timestamp": get_epoch(dep.metadata.creation_timestamp),
                "deletion_timestamp": get_epoch(dep.metadata.deletion_timestamp),
                "namespace": dep.metadata.namespace,
                "labels": _format_labels(dep.metadata.labels),
                "replicas": dep.spec.replicas if dep.spec else None,
                "available_replicas": dep.status.available_replicas if dep.status else None,
                "ready_replicas": dep.status.ready_replicas if dep.status else None,
                "updated_replicas": dep.status.updated_replicas if dep.status else None,
                "service_account": dep.spec.template.spec.service_account_name if dep.spec and dep.spec.template and dep.spec.template.spec else None,
                "configmaps": configmaps,
                "secrets": secrets,
            }
        )
    return transformed


@timeit
def load_deployments(
    session: neo4j.Session,
    deployments: list[dict[str, Any]],
    update_tag: int,
    cluster_id: str,
    cluster_name: str,
) -> None:
    logger.info(f"Loading {len(deployments)} kubernetes deployments.")
    load(
        session,
        KubernetesDeploymentSchema(),
        deployments,
        lastupdated=update_tag,
        CLUSTER_ID=cluster_id,
        CLUSTER_NAME=cluster_name,
    )


@timeit
def cleanup(session: neo4j.Session, common_job_parameters: dict[str, Any]) -> None:
    logger.debug("Running cleanup job for KubernetesDeployment")
    cleanup_job = GraphJob.from_node_schema(
        KubernetesDeploymentSchema(), common_job_parameters
    )
    cleanup_job.run(session)


@timeit
def sync_deployments(
    session: neo4j.Session,
    client: K8sClient,
    update_tag: int,
    common_job_parameters: dict[str, Any],
) -> list[dict[str, Any]]:
    deployments = get_deployments(client)
    transformed_deployments = transform_deployments(deployments)
    load_deployments(
        session=session,
        deployments=transformed_deployments,
        update_tag=update_tag,
        cluster_id=common_job_parameters["CLUSTER_ID"],
        cluster_name=client.name,
    )
    cleanup(session, common_job_parameters)
    return transformed_deployments
