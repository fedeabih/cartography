from dataclasses import dataclass

from cartography.models.core.common import PropertyRef
from cartography.models.core.nodes import CartographyNodeProperties
from cartography.models.core.nodes import CartographyNodeSchema
from cartography.models.core.relationships import CartographyRelProperties
from cartography.models.core.relationships import CartographyRelSchema
from cartography.models.core.relationships import LinkDirection
from cartography.models.core.relationships import make_target_node_matcher
from cartography.models.core.relationships import OtherRelationships
from cartography.models.core.relationships import TargetNodeMatcher


@dataclass(frozen=True)
class KubernetesDeploymentNodeProperties(CartographyNodeProperties):
    id: PropertyRef = PropertyRef("uid")
    name: PropertyRef = PropertyRef("name", extra_index=True)
    creation_timestamp: PropertyRef = PropertyRef("creation_timestamp")
    deletion_timestamp: PropertyRef = PropertyRef("deletion_timestamp")
    namespace: PropertyRef = PropertyRef("namespace", extra_index=True)
    labels: PropertyRef = PropertyRef("labels")
    replicas: PropertyRef = PropertyRef("replicas")
    available_replicas: PropertyRef = PropertyRef("available_replicas")
    ready_replicas: PropertyRef = PropertyRef("ready_replicas")
    updated_replicas: PropertyRef = PropertyRef("updated_replicas")
    service_account: PropertyRef = PropertyRef("service_account")
    configmaps: PropertyRef = PropertyRef("configmaps")
    secrets: PropertyRef = PropertyRef("secrets")
    cluster_name: PropertyRef = PropertyRef(
        "CLUSTER_NAME", set_in_kwargs=True, extra_index=True
    )
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
class KubernetesDeploymentToKubernetesNamespaceRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesDeployment)<-[:CONTAINS]-(:KubernetesNamespace)
class KubernetesDeploymentToKubernetesNamespaceRel(CartographyRelSchema):
    target_node_label: str = "KubernetesNamespace"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "name": PropertyRef("namespace"),
        }
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "CONTAINS"
    properties: KubernetesDeploymentToKubernetesNamespaceRelProperties = (
        KubernetesDeploymentToKubernetesNamespaceRelProperties()
    )


@dataclass(frozen=True)
class KubernetesDeploymentToKubernetesClusterRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesDeployment)<-[:RESOURCE]-(:KubernetesCluster)
class KubernetesDeploymentToKubernetesClusterRel(CartographyRelSchema):
    target_node_label: str = "KubernetesCluster"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {"id": PropertyRef("CLUSTER_ID", set_in_kwargs=True)}
    )
    direction: LinkDirection = LinkDirection.INWARD
    rel_label: str = "RESOURCE"
    properties: KubernetesDeploymentToKubernetesClusterRelProperties = (
        KubernetesDeploymentToKubernetesClusterRelProperties()
    )


@dataclass(frozen=True)
class KubernetesDeploymentToConfigMapRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesDeployment)<-[:USES_CONFIGMAP]-(:KubernetesConfigMap)
class KubernetesDeploymentToConfigMapRel(CartographyRelSchema):
    target_node_label: str = "KubernetesConfigMap"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "name": PropertyRef("configmaps", set_in_property=True),
            "namespace": PropertyRef("namespace"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_CONFIGMAP"
    properties: KubernetesDeploymentToConfigMapRelProperties = (
        KubernetesDeploymentToConfigMapRelProperties()
    )


@dataclass(frozen=True)
class KubernetesDeploymentToSecretRelProperties(CartographyRelProperties):
    lastupdated: PropertyRef = PropertyRef("lastupdated", set_in_kwargs=True)


@dataclass(frozen=True)
# (:KubernetesDeployment)<-[:USES_SECRET]-(:KubernetesSecret)
class KubernetesDeploymentToSecretRel(CartographyRelSchema):
    target_node_label: str = "KubernetesSecret"
    target_node_matcher: TargetNodeMatcher = make_target_node_matcher(
        {
            "cluster_name": PropertyRef("CLUSTER_NAME", set_in_kwargs=True),
            "name": PropertyRef("secrets", set_in_property=True),
            "namespace": PropertyRef("namespace"),
        }
    )
    direction: LinkDirection = LinkDirection.OUTWARD
    rel_label: str = "USES_SECRET"
    properties: KubernetesDeploymentToSecretRelProperties = (
        KubernetesDeploymentToSecretRelProperties()
    )


@dataclass(frozen=True)
class KubernetesDeploymentSchema(CartographyNodeSchema):
    label: str = "KubernetesDeployment"
    properties: KubernetesDeploymentNodeProperties = KubernetesDeploymentNodeProperties()
    sub_resource_relationship: KubernetesDeploymentToKubernetesClusterRel = (
        KubernetesDeploymentToKubernetesClusterRel()
    )
    other_relationships: OtherRelationships = OtherRelationships(
        [
            KubernetesDeploymentToKubernetesNamespaceRel(),
            KubernetesDeploymentToConfigMapRel(),
            KubernetesDeploymentToSecretRel(),
        ]
    )
