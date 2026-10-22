# Deployments

A Deployment manages a replicated set of Pods and supports declarative updates and rollbacks.

## Example

This Deployment runs three NGINX Pods and exposes container port `80`.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  namespace: demo
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: nginx
          image: nginx:1.27
          ports:
            - containerPort: 80
          readinessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 10
```

## Useful Commands

```bash
kubectl apply -f deployment.yaml
kubectl get deployments
kubectl get pods -l app=web
kubectl scale deployment web --replicas=5
kubectl set image deployment/web nginx=nginx:1.28
kubectl rollout restart deployment <name>
kubectl rollout status deployment <name>
kubectl rollout history deployment <name>
kubectl rollout undo deployment <name>
```

If Pods do not become ready, inspect the Deployment and Pods with
`kubectl describe`, then review container logs with `kubectl logs <pod-name>`.
