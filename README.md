# UCSD Buyer Review Multi Agent System (MAS)


## Table of Contents
- [Collaboration](#collaboration)
- [Disclaimers](#disclaimers)
- [Overview](#MAS-overview)
- [Deployment Steps](#deployment-steps)



# Collaboration
Thanks for your interest in our solution.  Having specific examples of replication and cloning allows us to continue to grow and scale our work. If you
 clone or download this repository, kindly shoot us a quick email to let us know you are interested in this work!

[wwps-cic@amazon.com]

# Disclaimers

**Customers are responsible for making their own independent assessment of the information in this document.**

**This document:**

(a) is for informational purposes only,

(b) represents current AWS product offerings and practices, which are subject to change without notice, and

(c) does not create any commitments or assurances from AWS and its affiliates, suppliers or licensors. AWS products or services are provided “as is” without warranties, representations, or conditions of any kind, whether express or implied. The responsibilities and liabilities of AWS to its customers a
re controlled by AWS agreements, and this document is not part of, nor does it modify, any agreement between AWS and its customers.

(d) is not to be considered a recommendation or viewpoint of AWS

**Additionally, all prototype code and associated assets should be considered:**

(a) as-is and without warranties

(b) not suitable for production environments

(d) to include shortcuts in order to support rapid prototyping such as, but not limitted to, relaxed authentication and authorization and a lack of str
ict adherence to security best practices

**All work produced is open source. More information can be found in the GitHub repo.**

## PO Workflow automation overview
- The [DxHub](https://dxhub.calpoly.edu/challenges/) developed an agentic solution that takes in documents detailing a specific purcahse order and outp
uts a list of checks. This workflow contains many agents:

    #### Document Parser Agent
    - Classifies document type and uses tooling to determine which prompt to use to parse each document
    - Parses each document and resturns to a state for all agents to use

    #### Data Security Classification Agent
    - Classifies documents into security tiers (P1–P4) for data sensitivity.
    - Uses LLM reasoning to detect sensitive content in service information
    - Returns structured JSON indicating the classification level and reasoning behind it.

    #### Purchasing Categories Mapping Agent
    - Classifies each purchase order into a purchasing category using an LLM to reason

    #### PHI Agreement Check Agent
    - Determines if PHI (Protected Health Information) exists in purcahse order documents.
    - Scans text for HIPAA-related clauses and required agreement language.

    #### Summarization Agent
    - Takes all checks from previous agents and generates a summary document that includes all the checks


## Deployment Steps

### Prerequisites
- AWS CDK CLI, Docker (running), Python 3.x, Git, a CDK Bootstrapped environment
- AWS credentials configured

### Step 1: Clone & Setup
```bash
git clone https://github.com/cal-poly-dxhub/university-buyerreview.git
cd university-buyerreview
```

### Step 2: Request Bedrock Model Access
In AWS Bedrock console → Model access, request access for:
- `anthropic.claude-3-5-sonnet-20241022-v2:0`

### Step 3: Deploy Infrastructure
```bash
cd university-buyerreview/cdk
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cdk deploy
```

### Step 4: Upload Documents & Run Processing

#### Step 1:
In the AWS console, upload the purchase order documents to the s3 bucket named 077938161517-us-west-2-dxhub-ub-bkt)
Then retrieve the s3 uris from each document

#### Step 2:
Use the following command to list your REST APIs and find the id of the 'document-processing' API.
```bash
aws apigateway get-rest-apis
```

Your invoke URL will be the following
```bash
https://<restApiId>.execute-api.<region>.amazonaws.com/prod/process
```

#### Step 3:
Then invoke the API with the invoke URL and the s3 uris retrieved earlier
```bash
curl -X POST \
  "https://<restApiId>.execute-api.<region>.amazonaws.com/prod/process" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "1756845945-5374f12e",
    "s3_uris": [<your-s3-uris>],
    "metadata": {}
  }'
```

#### Step 4:
Once the API is invoked, the resulting summary document should be uploaded to the 077938161517-us-west-2-dxhub-results-bkt s3 bucket once the workflow is ran through. It should take 3-4 minutes.



## Troubleshooting
- **Docker access**: `sudo usermod -aG docker $USER && newgrp docker`
- **CDK issues**: Check `aws sts get-caller-identity` and run `cdk bootstrap`
- **Model access**: Verify in Bedrock console
- **Processing fails**: Check Step Function logs in AWS Console
- **Chat issues**: Verify API key and endpoint accessibility

## Known Issues
- Quick PoC with no intent verification or error checking

## Support
For queries or issues:
- Darren Kraker, Sr Solutions Architect - dkraker@amazon.com
- Maciej Zukowski, Software Development Engineer - zukomaci@amazon.com
- Adarsh Murugesan, Software Development Engineer Intern - admuruge@calpoly.edu
- Belal Elshenety, Software Development Engineer Intern - belshene@calpoly.edu
- Noor Dhaliwal, Software Development Engineer Intern - rdhali07@calpoly.edu