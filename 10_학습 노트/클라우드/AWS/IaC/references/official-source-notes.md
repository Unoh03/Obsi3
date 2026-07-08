# v6.1 공식 근거 메모

- AWS Gateway Endpoint:
  - https://docs.aws.amazon.com/vpc/latest/privatelink/gateway-endpoints.html
  - Gateway VPC endpoints provide connectivity to Amazon S3 and DynamoDB without requiring an Internet Gateway or NAT device.
  - Gateway endpoint route tables use AWS-managed service prefix lists and the endpoint target.
- AWS S3 Gateway Endpoint:
  - https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints-s3.html
  - S3 Gateway Endpoint can be used from a VPC without IGW/NAT and security groups can reference the S3 prefix list.
- Amazon Linux 2023 package management:
  - https://docs.aws.amazon.com/linux/al2023/ug/package-management.html
  - AL2023 uses DNF; yum is a pointer to DNF.
- AL2023 deterministic repositories:
  - https://docs.aws.amazon.com/linux/al2023/ug/deterministic-upgrades-usage.html
  - AWS examples show amazon-linux-repo-s3 in AL2023 repository upgrade flow.
