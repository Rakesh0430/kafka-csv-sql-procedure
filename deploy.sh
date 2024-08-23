#!/bin/bash

# Set up variables
RESOURCE_GROUP="GenAI-RG" # Using your provided resource group
LOCATION="eastus"
APP_NAME="csvtoxml-app"
APP_PLAN="csvtoxml-plan"
ACR_NAME="csvtoxmlregistry"

# Assuming the following:
# - You have already built and pushed your Docker image to ACR
# - The image is named 'csvtoxml:v1'
# - The ACR is already created and you're logged in

# Create an App Service plan (if it doesn't exist)
az appservice plan create --name $APP_PLAN --resource-group $RESOURCE_GROUP --is-linux --sku B1

# Create a web app
az webapp create --resource-group $RESOURCE_GROUP --plan $APP_PLAN --name $APP_NAME --deployment-container-image-name "${ACR_NAME}.azurecr.io/csvtoxml:v1"

# Configure the web app to use the ACR image
az webapp config container set --name $APP_NAME --resource-group $RESOURCE_GROUP --docker-custom-image-name "${ACR_NAME}.azurecr.io/csvtoxml:v1" --docker-registry-server-url "https://${ACR_NAME}.azurecr.io"

# Enable system-assigned managed identity for the web app
az webapp identity assign --resource-group $RESOURCE_GROUP --name $APP_NAME

# Get the principal ID of the web app's managed identity
PRINCIPAL_ID=$(az webapp identity show --resource-group $RESOURCE_GROUP --name $APP_NAME --query principalId --output tsv)

# Get the resource ID of the ACR
ACR_ID=$(az acr show --resource-group $RESOURCE_GROUP --name $ACR_NAME --query id --output tsv)

# Assign AcrPull role to the web app for the ACR
az role assignment create --assignee $PRINCIPAL_ID --scope $ACR_ID --role AcrPull

# Configure the web app to use the managed identity for ACR pulls
az webapp config container set --name $APP_NAME --resource-group $RESOURCE_GROUP --docker-custom-image-name "${ACR_NAME}.azurecr.io/csvtoxml:v1" --docker-registry-server-url "https://${ACR_NAME}.azurecr.io" --docker-registry-server-user "" --docker-registry-server-password ""

echo "Deployment complete. Your app should be available at: https://$APP_NAME.azurewebsites.net"