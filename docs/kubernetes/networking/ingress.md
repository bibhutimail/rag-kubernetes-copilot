# Ingress

An Ingress exposes HTTP and HTTPS routes from outside a Kubernetes cluster to services inside the cluster. An Ingress controller must be installed for Ingress resources to take effect.

## Example

This resource routes requests for `app.example.com` to the `web-service`
Service on port `80`.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-ingress
  namespace: demo
spec:
  ingressClassName: nginx
  rules:
    - host: app.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: web-service
                port:
                  number: 80
```

## Useful Commands

```bash
kubectl apply -f ingress.yaml
kubectl get ingress
kubectl describe ingress <name>
```

If the Ingress has no address or does not route traffic, verify that an Ingress
controller is running, the `ingressClassName` is correct, and the backend
Service and endpoints exist.
