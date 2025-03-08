# Installation of Minikube, Kubectl, and ArgoCD

## Install minikube:

* curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
* sudo install kubectl /usr/local/bin/

## start minikube:

* minikube start
* kubectl get nodes

## Install kubectx
* sudo apt install -y kubectx

## Install helm
* curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

## Install argo:

* helm repo add argo https://argoproj.github.io/argo-helm

* helm repo update
* helm install argocd argo/argo-cd --namespace argocd --create-namespace

## Check/Verify argocd
* kubectl get pods -n argocd

## Portforwarding 
kubectl port-forward service/argocd-server -n argocd 8080:443
