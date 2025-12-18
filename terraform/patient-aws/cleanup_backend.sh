#!/bin/bash
BUCKET="cloud-doctor-tfstate-selffish234"

echo "Listing and deleting object versions..."
# List versions. If empty, it returns nothing.
aws s3api list-object-versions --bucket $BUCKET --query 'Versions[].{Key:Key,VersionId:VersionId}' --output text | while read KEY VER; do 
    if [ "$KEY" != "None" ] && [ -n "$KEY" ]; then
        echo "Deleting object: $KEY (Version: $VER)"
        aws s3api delete-object --bucket $BUCKET --key "$KEY" --version-id "$VER"
    fi
done

echo "Listing and deleting delete markers..."
# List delete markers.
aws s3api list-object-versions --bucket $BUCKET --query 'DeleteMarkers[].{Key:Key,VersionId:VersionId}' --output text | while read KEY VER; do 
    if [ "$KEY" != "None" ] && [ -n "$KEY" ]; then
        echo "Deleting marker: $KEY (Version: $VER)"
        aws s3api delete-object --bucket $BUCKET --key "$KEY" --version-id "$VER"
    fi
done

echo "Deleting bucket..."
aws s3 rb s3://$BUCKET
