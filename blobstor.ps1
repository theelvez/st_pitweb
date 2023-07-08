# Set variables
storageAccountName="pitwebStorage"
storageContainerName="<pitwebStorageContainer>"

# Create a storage account
az storage account create --name $storageAccountName --resource-group <resource_group_name> --location <location> --sku Standard_LRS

# Retrieve the storage account connection string
connectionString=$(az storage account show-connection-string --name $storageAccountName --resource-group <resource_group_name> --query connectionString --output tsv)

# Create a storage container
az storage container create --name $storageContainerName --connection-string $connectionString
