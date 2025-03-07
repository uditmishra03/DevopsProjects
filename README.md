# Installation of Minikube, Kubectl, and ArgoCD


curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube


install minikube:

curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install kubectl /usr/local/bin/
kubectl version --client

start minikube:

minikube start
kubectl get nodes

sudo apt install -y kubectx


curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash


install argo:

helm repo add argo https://argoproj.github.io/argo-helm

helm repo update
helm install argocd argo/argo-cd --namespace argocd --create-namespace


kubectl get pods -n argocd

kubectl port-forward service/argocd-server -n argocd 8080:443
