#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <password> <IP:port> <port>"
    exit 1
fi

# Assign input arguments to variables
password=$1
ip_port=$2
port=$3

# Construct the BKC URL
url="https://$ip_port:8080/$port/hmc/redfish/v1/UpdateService/FirmwareInventory/bundle_active"

# Construct the IFWI URL
url2="https://$ip_port:8080/$port/hmc/redfish/v1/UpdateService/FirmwareInventory/ifwi_active"

# Commands to query BKC version on banff systems
response=$(curl -kis -u root:"$password" -X GET "$url")

# Commands to query IFWI version on banff systems
response2=$(curl -kis -u root:"$password" -X GET "$url2")


# Extract Version and ComponentDetails
version=$(echo "$response" | grep -oP '"Version":\s*"\K[^"]+')
component_details=$(echo "$response" | grep -oP '"ComponentDetails":\s*"\K[^"]+')

version2=$(echo "$response2" | grep -oP '"Version":\s*"\K[^"]+')
component_details2=$(echo "$response2" | grep -oP '"ComponentDetails":\s*"\K[^"]+')


# Get ROCM version and AMD GPU driver vers
Rocmversion=$(cat /opt/rocm/.info/version)

AMDGPUdriverversion=$(dkms status | grep amdgpu | cut -d',' -f1)


# Print the extracted values
echo "BKC Version: $version"
echo "BKC ComponentDetails: $component_details"

echo "IFWI Version: $version2"
echo "IFWI ComponentDetails: $component_details2"

echo "ROCm Version: $Rocmversion"
echo "AMDGPU Driver Version: $AMDGPUdriverversion"