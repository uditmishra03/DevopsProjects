# Installation of Minikube, Kubectl, and ArgoCD

## Install minikube:

* curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
* sudo install minikube-linux-amd64 /usr/local/bin/minikube

## Install Kubectl:

* curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

* sudo install kubectl /usr/local/bin/

### Check kubectl installation: 
* kubectl version --client

## start minikube:

* minikube start
* kubectl get nodes

## Install kubectx

  Install Dependencies
* sudo dnf install -y git bash-completion
  Clone the kubectx Repository
* git clone https://github.com/ahmetb/kubectx.git ~/.kubectx

### Add kubens to Your PATH
* echo 'export PATH=$HOME/.kubectx:$PATH' >> ~/.bashrc
* source ~/.bashrc

### Verify Installation
* kubens --help


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
