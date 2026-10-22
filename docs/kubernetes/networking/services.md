# Services

A Service provides a stable network endpoint for a group of Pods selected by labels. Common service types are `ClusterIP`, `NodePort`, `LoadBalancer`, and `ExternalName`.

## Service Types

- `ClusterIP`: exposes the Service only inside the cluster.
- `NodePort`: exposes the Service on a port on every node.
- `LoadBalancer`: requests an external load balancer from the infrastructure provider.
- `ExternalName`: maps the Service to an external DNS name.

## Example

This Service sends traffic on port `80` to port `8080` on Pods labeled
`app: web`.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-service
  namespace: demo
spec:
  type: ClusterIP
  selector:
    app: web
  ports:
    - name: http
      port: 80
      targetPort: 8080
```

## Useful Commands

```bash
kubectl apply -f service.yaml
kubectl get services
kubectl describe service <name>
kubectl get endpoints <name>
```

If a Service has no endpoints, confirm that its selector matches the labels on
running and ready Pods.
