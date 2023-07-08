$storageAccountName = "pitwebstorage"
$storageContainerName = "pitwebstoragecontainer"

az storage account create --name $storageAccountName --resource-group "pitwebResources" --location "westus" --sku Standard_LRS

$connectionString = az storage account show-connection-string --name $storageAccountName --resource-group pitwebResources --query connectionString --output tsv

az storage container create --name $storageContainerName --connection-string $connectionString
