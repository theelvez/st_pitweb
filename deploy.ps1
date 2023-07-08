# Variables
$appName = "pitweb"  # Replace with your app name
$resourceGroup = "pitwebResources"  # Replace with your resource group name
$location = "westus"  # Replace with your location (e.g., westus)
$planName = $appName + "ServicePlan"
$runtime = "PYTHON|3.10"  # Replace with your Python version

# Create a resource group
az group create --name $resourceGroup --location $location

# Create an App Service plan
az appservice plan create --name $planName --resource-group $resourceGroup --sku B1 --is-linux

# Create a web app
az webapp create --name $appName --resource-group $resourceGroup --plan $planName --runtime $runtime

# Configure the web app to use local git for deployment
az webapp deployment source config-local-git --name $appName --resource-group $resourceGroup

# Get the deployment URL
$url = az webapp deployment source config-local-git --name $appName --resource-group $resourceGroup --query url --output tsv

Write-Host "Your deployment URL is: $url"

# Push to the Azure remote repository
git remote add azure $url
git push azure master
