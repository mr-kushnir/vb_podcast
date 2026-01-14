#!/usr/bin/env python3
"""Update POD-6 task with deployment results"""

import sys
sys.path.insert(0, 'scripts')

from youtrack import YouTrackClient

def main():
    client = YouTrackClient()

    # Update state to Done
    print("Updating POD-6 state to Done...")
    result = client.update_issue_state("POD-6", "Done")
    print(f"State updated: {result}")

    # Add deployment summary comment
    comment = """✅ **Deployment completed successfully!**

**Deployed Resources:**
- **Serverless Container**: https://bba6vo668ro691778vpr.containers.yandexcloud.net/
- **YDB Database**: exam-podvbpodcast-db (4 tables created)
- **S3 Bucket**: exam-podvbpodcast-files (1GB)
- **API Gateway**: https://d5d5eve4c48hitvjardl.z7jmlavt.apigw.yandexcloud.net/
- **Daily Cron Trigger**: ACTIVE (7:00 UTC)
- **Service Account**: exam-podvbpodcast-sa

**Health Check**: PASSING ✅
**All API endpoints**: Working ✅
**Automation endpoint**: `/api/automation/generate` - tested ✅

**Custom Domain (podcast.rapidapp.ru):**
- Certificate requested: fpqka060atj58unfj0me (VALIDATING)
- Awaiting DNS configuration (CNAME records)

**Cost Estimate**: ~$5-8/month

**Documentation**:
- Full guide: [DEPLOYMENT_SUCCESS.md](https://github.com/mr-kushnir/vb_podcast/blob/main/DEPLOYMENT_SUCCESS.md)
- Quick start: [README_DEPLOY.md](https://github.com/mr-kushnir/vb_podcast/blob/main/README_DEPLOY.md)

**Next Steps**:
1. Configure DNS for custom domain
2. Test full podcast generation pipeline
3. Monitor first automated generation at 7:00 UTC tomorrow
"""

    print("Adding deployment summary comment...")
    result = client.add_comment("POD-6", comment)
    print(f"Comment added: {result}")

    print("\n✅ POD-6 updated successfully!")

if __name__ == "__main__":
    main()
