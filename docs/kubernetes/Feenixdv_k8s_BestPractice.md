# Feenixdv Kubernetes CIS Best Practices

This guide provides a practical Kubernetes security baseline aligned with the
areas assessed by the CIS Kubernetes Benchmark. CIS recommendations and control
numbers can change between benchmark and Kubernetes versions. Before an audit,
download the current benchmark from CIS and validate every setting against the
exact Kubernetes distribution and version in use.

For managed Kubernetes services, the cloud provider usually owns some control
plane checks. Record those checks as provider-managed rather than changing
components that the service does not expose.

## 1. Governance and Access

- Maintain separate development, test, and production clusters.
- Require centralized identity, MFA, short-lived credentials, and individual
  user accounts. Do not share kubeconfig files or service-account tokens.
- Grant access through RBAC groups and namespace-scoped Roles where possible.
- Avoid routine use of `cluster-admin`, wildcard permissions, and direct grants
  to users.
- Bind privileged service accounts only to workloads that need them.
- Disable automatic service-account token mounting by default:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: application
  namespace: production
automountServiceAccountToken: false
```

- Review access regularly:

```bash
kubectl auth can-i --list --namespace production
kubectl get clusterrolebindings
kubectl get rolebindings --all-namespaces
```

## 2. API Server and Control Plane

Configure the API server according to the current CIS benchmark:

- Disable anonymous authentication.
- Use `Node` and `RBAC` authorization.
- Enable the `NodeRestriction` admission plugin.
- Disable profiling unless it is temporarily required for troubleshooting.
- Use trusted TLS certificates and restrict weak TLS cipher suites.
- Configure request timeouts and admission controls appropriate to the cluster.
- Enable audit logging with a documented audit policy, log rotation, restricted
  file permissions, and centralized retention.
- Encrypt Kubernetes Secrets at rest with a KMS provider where available.
- Restrict network access to the API endpoint to approved administrative
  networks and private connectivity.

Example audit policy:

```yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  - level: Metadata
    resources:
      - group: ""
        resources: ["secrets", "configmaps"]
  - level: RequestResponse
    resources:
      - group: "rbac.authorization.k8s.io"
        resources: ["roles", "rolebindings", "clusterroles", "clusterrolebindings"]
  - level: Metadata
```

Do not log Secret values or other sensitive request bodies unless a documented
investigation requires it.

## 3. etcd Protection

- Permit access to etcd only from control plane hosts.
- Require trusted client certificates and peer certificates.
- Enable client and peer certificate authentication.
- Protect etcd data directories and certificate files with the restrictive
  ownership and permissions required by the applicable CIS benchmark.
- Encrypt sensitive API data before it is stored in etcd.
- Back up etcd regularly, encrypt backups, restrict backup access, and test
  restoration procedures.
- Rotate etcd certificates before expiration.

Never expose the etcd client port to public or general workload networks.

## 4. Controller Manager and Scheduler

- Bind health and metrics endpoints to loopback or protected interfaces.
- Use TLS for component communication.
- Give each control plane component a dedicated identity and minimum RBAC
  permissions.
- Enable service-account credential rotation and use a securely protected
  service-account signing key.
- Configure terminated Pod garbage collection to prevent unnecessary resource
  accumulation.

## 5. Kubelet and Worker Nodes

Use a secured kubelet configuration on every node:

```yaml
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
authentication:
  anonymous:
    enabled: false
  webhook:
    enabled: true
authorization:
  mode: Webhook
readOnlyPort: 0
protectKernelDefaults: true
rotateCertificates: true
serverTLSBootstrap: true
```

Also apply these controls:

- Do not expose kubelet ports to untrusted networks.
- Use a supported and patched operating system, container runtime, and
  Kubernetes release.
- Restrict SSH access, disable password login, and use audited administrative
  access.
- Apply CIS operating-system benchmarks to worker nodes where applicable.
- Protect kubelet configuration, PKI, and kubeconfig files with the ownership
  and permissions specified by the benchmark.
- Use dedicated node pools, taints, and tolerations to isolate sensitive
  workloads.
- Keep control plane nodes free of ordinary application workloads.

## 6. Pod Security

Enforce Kubernetes Pod Security Standards at the namespace level. New
application namespaces should use the `restricted` profile unless a documented
exception is approved.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

Use a restrictive security context:

```yaml
securityContext:
  runAsNonRoot: true
  seccompProfile:
    type: RuntimeDefault
containers:
  - name: app
    image: registry.example.com/team/app@sha256:REPLACE_WITH_DIGEST
    securityContext:
      allowPrivilegeEscalation: false
      privileged: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
          - ALL
```

Do not allow privileged containers, host PID/IPC/network namespaces,
`hostPath` volumes, added Linux capabilities, or running as root without a
reviewed and time-limited exception.

## 7. Network Security

- Apply default-deny ingress and egress NetworkPolicies to every application
  namespace, then allow only required traffic.
- Separate sensitive workloads into dedicated namespaces and node pools.
- Restrict access to cloud instance metadata endpoints.
- Use TLS for service-to-service traffic that crosses trust boundaries.
- Limit LoadBalancer and NodePort Services; expose applications through
  approved ingress gateways.

Example default-deny policy:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: production
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
```

Confirm that the installed CNI plugin enforces NetworkPolicy.

## 8. Secrets and Workload Configuration

- Store credentials in an approved external secret manager where practical.
- Never commit Secrets, kubeconfig files, private keys, or tokens to source
  control.
- Encrypt Secrets at rest and in backups.
- Mount sensitive values as files with restricted permissions where possible,
  and avoid exposing them in command-line arguments or logs.
- Rotate credentials automatically and after personnel or workload changes.
- Set CPU and memory requests and limits to reduce resource exhaustion risk.
- Configure readiness, liveness, and startup probes for production workloads.

## 9. Image and Supply-Chain Security

- Pull images only from approved private registries.
- Pin production images by immutable digest rather than a mutable tag.
- Scan images for known vulnerabilities and block releases that violate the
  organization's severity policy.
- Generate and retain an SBOM, sign release images, and verify signatures during
  admission.
- Use minimal, non-root images without unnecessary shells or package managers.
- Restrict image-pull credentials to the required namespace and registry.

These controls complement the CIS Kubernetes Benchmark and should be included
in the broader implementation standard.

## 10. Logging, Monitoring, and Incident Readiness

- Send API audit, control plane, node, workload, and security logs to a
  centralized, access-controlled platform.
- Alert on privileged Pod creation, RBAC changes, failed authentication,
  exec/attach activity, Secret access, and disabled security controls.
- Monitor certificate expiration, node health, resource pressure, and abnormal
  workload behavior.
- Synchronize node time and protect log integrity.
- Document procedures to isolate nodes, revoke credentials, preserve evidence,
  rotate Secrets, and rebuild compromised workloads.

## 11. CIS Assessment

Run a version-compatible CIS assessment tool such as `kube-bench` from a trusted
source. Select the benchmark profile that matches the cluster distribution and
version.

```bash
kube-bench version
kube-bench run
```

For every result:

1. Confirm that the check applies to the cluster and ownership model.
2. Review the current CIS remediation guidance before making a change.
3. Test the change in a non-production environment.
4. Record evidence, owner, date, status, and any approved exception.
5. Re-run the check and retain the report.

Do not apply automated remediations blindly. Some CIS settings can disrupt
cluster networking, authentication, admission, or managed control plane
operations.

## 12. Implementation Checklist

- [ ] Cluster and benchmark versions are documented.
- [ ] Control ownership is split between Feenixdv and the platform provider.
- [ ] API endpoint access is private or allow-listed.
- [ ] Anonymous access is disabled and RBAC is enforced.
- [ ] Audit logging and centralized retention are enabled.
- [ ] Secrets are encrypted at rest and credentials are rotated.
- [ ] etcd is isolated, authenticated, backed up, and restore-tested.
- [ ] Kubelet anonymous access and read-only ports are disabled.
- [ ] Nodes and Kubernetes components are supported and patched.
- [ ] Pod Security `restricted` is enforced or exceptions are documented.
- [ ] Default-deny NetworkPolicies are applied and tested.
- [ ] Production containers run as non-root with minimal privileges.
- [ ] Images are scanned, signed, and pinned by digest.
- [ ] CIS scans run after provisioning, upgrades, and material configuration changes.
- [ ] Failed checks have owners, deadlines, evidence, or approved exceptions.

## References

- CIS Kubernetes Benchmark for the applicable Kubernetes version and distribution
- Kubernetes Pod Security Standards
- Kubernetes security checklist
- Kubernetes audit logging documentation
- Kubernetes RBAC good practices
