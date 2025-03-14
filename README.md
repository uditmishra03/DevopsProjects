# DevOps Projects - PresyncArgo

## Overview
The `PresyncArgo` branch of this repository is dedicated to demonstrating the use of **PreSync hooks in ArgoCD**. PreSync hooks allow executing custom commands or scripts **before** Kubernetes manifests are applied, making them useful for tasks like database migrations, checking dependencies, or initializing resources before deployment.

## Key Features
- **PreSync Hook Execution**: Ensures necessary tasks are completed before the actual deployment starts.
- **ArgoCD GitOps Workflow**: Enables declarative, automated deployments.
- **Helm Chart Integration**: Uses Helm to template Kubernetes resources.
- **CI/CD Automation**: Can be integrated into pipelines for continuous deployment.
- **Kubernetes Resource Management**: Structured and reusable Kubernetes configurations.

## Prerequisites
Ensure you have the following installed:
- **Kubernetes Cluster** (Minikube, Kind, EKS, AKS, GKE, etc.)
- **ArgoCD** (`kubectl` access and ArgoCD CLI)
- **Helm** (for templating)
- **Git** (for repository management)

## Setup and Deployment
1. **Clone the Repository**
   ```sh
   git clone -b PresyncArgo https://github.com/uditmishra03/DevopsProjects.git
   cd DevopsProjects
   ```
2. **Install ArgoCD** (if not already installed)
   ```sh
   kubectl create namespace argocd
   kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
   ```
3. **Login to ArgoCD CLI**
   ```sh
   argocd login <ARGOCD_SERVER> --username admin --password <YOUR_PASSWORD>
   ```
4. **Deploy the ArgoCD Application with PreSync Hook**
   ```sh
   kubectl apply -f presync-argocd-app.yaml
   ```
5. **Sync the Application**
   ```sh
   argocd app sync presync-app
   ```

## How PreSync Hooks Work in This Branch
- **The `argocd-app.yaml` file** contains an ArgoCD application definition with a **PreSync hook**.
- The PreSync hook runs a **custom script** or command before the application is applied.
- Useful for running database migrations, setting up external dependencies, or validating conditions before deployment.

### Example: PreSync Hook in `argocd-app.yaml`
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: presync-job
  annotations:
    argocd.argoproj.io/hook: PreSync
spec:
  template:
    spec:
      containers:
      - name: prehook
        image: busybox
        command: ["sh", "-c", "echo Running PreSync Hook"]
      restartPolicy: Never
```
This ensures that `echo Running PreSync Hook` executes **before** applying other resources.

## Directory Structure
```
DevopsProjects/
│── manifests/              # Kubernetes YAMLs specific to PresyncArgo
│── helm-charts/            # Helm chart for ArgoCD application
│── presync-argocd-app.yaml # ArgoCD app with PreSync hook
│── README.md               # Documentation for PresyncArgo branch
```

## Troubleshooting
- **Application not syncing?** Check logs with:
  ```sh
  argocd app get presync-app
  ```
- **PreSync hook not running?** Inspect job logs:
  ```sh
  kubectl logs -l job-name=presync-job
  ```
- **Check ArgoCD UI** at `http://<ARGOCD_SERVER>/` for errors.

## Contributing
Contributions are welcome! Feel free to submit pull requests specific to **PreSync hooks** and ArgoCD enhancements.

## License
This project is licensed under the MIT License.

---
_Developed & Maintained by [Udit Mishra](https://github.com/uditmishra03)_ 🚀

