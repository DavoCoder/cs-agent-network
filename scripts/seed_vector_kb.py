"""
Script to seed the Pinecone vector database with sample knowledge base articles.
Run this after setting up your Pinecone account and API key.
"""

from dotenv import load_dotenv
from langchain_core.documents import Document
from src.tools.vector_store import get_vector_store

load_dotenv()


def seed_billing_kb():
    """Seed billing knowledge base articles."""
    
    vector_store = get_vector_store()
    if vector_store is None:
        print("Vector store not available. Make sure Pinecone is configured.")
        return
    
    # Billing knowledge base documents for LLM application platform
    billing_docs = [
        Document(
            page_content="""
            Subscription Plans and Pricing
            
            Our platform offers several subscription tiers for developers building LLM applications:
            
            Free Tier:
            - Open source library usage (MIT/Apache 2.0 license)
            - 1,000 API credits per month
            - Community support via GitHub
            - Self-hosted deployment
            
            Pro Tier ($29/month):
            - Everything in Free
            - 100,000 API credits per month
            - Priority email support
            - Advanced analytics and monitoring
            - Cloud deployment option
            
            Business Tier ($99/month):
            - Everything in Pro
            - 500,000 API credits per month
            - Priority phone and email support
            - Team collaboration features
            - Custom integrations
            - SLA guarantee
            
            Enterprise (Custom pricing):
            - Unlimited API credits
            - Dedicated account manager
            - Custom agreements and SLAs
            - On-premise deployment
            - White-label options
            
            All plans include access to our open source libraries. Only cloud features and usage-based API credits require a paid subscription.
            """,
            metadata={
                "category": "billing",
                "topic": "pricing_plans",
                "type": "information"
            }
        ),
        Document(
            page_content="""
            API Credits and Usage-Based Billing
            
            API credits are consumed when using our cloud API services:
            - 1 credit = 1 API call
            - Credits reset monthly on your billing date
            - Unused credits do not roll over
            - Overage charges apply if you exceed your limit
            
            Overage charges (Pro plan):
            - First 100k credits: Included
            - Additional credits: $0.0003 per credit
            
            Tracking usage:
            1. Log into dashboard
            2. Navigate to Usage & Billing
            3. View real-time credit consumption
            
            To prevent overage:
            - Set up usage alerts in settings
            - Monitor dashboard regularly
            - Upgrade plan if consistently over limit
            
            Open source libraries can be used without consuming credits when self-hosting.
            """,
            metadata={
                "category": "billing",
                "topic": "api_credits",
                "type": "information"
            }
        ),
        Document(
            page_content="""
            Subscription Management
            
            To upgrade or downgrade your subscription:
            1. Log into your account
            2. Go to Settings > Billing > Subscription
            3. Click "Change Plan"
            4. Select new tier
            5. Confirm changes
            
            Changes take effect immediately, with prorated billing:
            - Downgrades: Credit to next billing cycle
            - Upgrades: Immediate access, prorated charge
            - Switch to annual plans: Immediate discount applied
            
            To cancel subscription:
            1. Settings > Billing > Subscription
            2. Click "Cancel Subscription"
            3. Choose immediate cancel or cancel at period end
            
            Note: Cancellation preserves open source library access. Only cloud features are disabled.
            
            Billing cycles: Monthly subscriptions renew on the same date each month.
            """,
            metadata={
                "category": "billing",
                "topic": "subscription_management",
                "type": "process"
            }
        ),
        Document(
            page_content="""
            Refund Policy
            
            Subscription-based SaaS refund policy:
            
            Eligibility:
            - Refunds available within 7 days of purchase for new subscriptions only
            - Partial refunds for annual plans if canceling mid-cycle (unused portion)
            - No refunds for usage-based charges (API credits consumed)
            
            Process:
            1. Contact support through dashboard
            2. Provide reason and account details
            3. Review within 2 business days
            4. If approved, refund issued within 5-7 business days
            
            Special circumstances:
            - Extended outages: We offer service credits
            - Billing errors: Immediate refund and correction
            - Duplicate charges: Full refund of duplicates
            
            Open source libraries: No refunds needed as they're free and open source.
            
            Refunds issued to original payment method only.
            """,
            metadata={
                "category": "billing",
                "topic": "refund_policy",
                "type": "policy"
            }
        ),
        Document(
            page_content="""
            Payment Issues and Failed Charges
            
            Common payment failure reasons:
            - Expired credit card
            - Insufficient funds
            - Card declined by bank
            - International payment restrictions
            
            What happens:
            - Service continues for 7 days after failed payment
            - Email notifications sent daily
            - Automatic retry after 3 days
            - Account suspended after 7 days if unpaid
            
            Resolution steps:
            1. Update payment method immediately
            2. Settings > Billing > Payment Methods
            3. Click "Update Card"
            4. Enter new payment details
            5. Save and verify
            
            If card continues to decline:
            - Contact your bank to allow recurring charges
            - Try alternative payment method
            - Contact support for manual payment processing
            
            Account restoration:
            - Immediate restoration once payment succeeds
            - No data loss during suspension
            - Usage history preserved
            """,
            metadata={
                "category": "billing",
                "topic": "payment_failures",
                "type": "troubleshooting"
            }
        ),
        Document(
            page_content="""
            Team and Seat Management
            
            Enterprise and Business plans support multiple team members:
            
            Adding team members:
            1. Settings > Team Management
            2. Click "Invite Member"
            3. Enter email and assign role
            4. User receives invitation email
            
            Roles and permissions:
            - Admin: Full access to billing and settings
            - Developer: API access, cannot modify billing
            - Viewer: Read-only dashboard access
            
            Seat limits:
            - Business: Up to 5 team members
            - Enterprise: Unlimited team members
            - Free/Pro: Single user accounts
            
            Seating charges (Business plan):
            - First 5 users included in subscription
            - Additional users: $10 per user per month
            
            Removing team members:
            1. Navigate to Team Management
            2. Click member to remove
            3. Click "Remove Access"
            4. Confirm removal
            
            Billing updates automatically based on seat count.
            """,
            metadata={
                "category": "billing",
                "topic": "team_management",
                "type": "process"
            }
        ),
        Document(
            page_content="""
            Open Source Licensing vs Paid Features
            
            Understanding what's free vs paid:
            
            Open Source (Always Free):
            - LLM application libraries (MIT/Apache 2.0)
            - GitHub repository access
            - Community documentation
            - Self-hosted deployment
            - Building and running applications locally
            - No credit consumption for local usage
            
            Paid Cloud Features (Requires Subscription):
            - Managed cloud API endpoints
            - Usage-based API credits
            - Team collaboration tools
            - Advanced monitoring and analytics
            - Priority support
            - SLA guarantees
            
            Mixing free and paid:
            - You can use open source libraries in paid applications
            - Cloud API usage requires paid subscription
            - Local development is always free
            - Production deployments can be self-hosted (free) or cloud (paid)
            
            Licensing for your applications:
            - You maintain full ownership of your code
            - Open source library license applies to library code only
            - Your application code remains your property
            - No revenue share or usage restrictions on your apps
            """,
            metadata={
                "category": "billing",
                "topic": "licensing",
                "type": "information"
            }
        ),
        Document(
            page_content="""
            Invoices and Export for Taxes
            
            Access billing documents:
            1. Log into dashboard
            2. Settings > Billing > Invoices
            3. View or download PDF invoices
            
            Invoice details include:
            - Invoice number and date
            - Subscription period
            - API usage breakdown (if applicable)
            - Amount charged
            - Payment method
            - Transaction ID
            - Tax information (if applicable)
            
            Exporting for accounting:
            - Download individual invoices as PDF
            - Export bulk invoice data as CSV
            - Transactions include line items for credits/usage
            
            Billing address updates:
            - Settings > Billing > Company Information
            - Update billing address for invoices
            - Changes reflect on next billing cycle
            
            International customers:
            - US customers: Sales tax applied in applicable states
            - International: Reverse charge applies (no VAT)
            - Enterprise customers: Custom invoicing available
            
            Available for 7 years for tax purposes.
            """,
            metadata={
                "category": "billing",
                "topic": "invoices_tax",
                "type": "information"
            }
        ),
        Document(
            page_content="""
            Enterprise Agreements and Custom Billing
            
            Enterprise customers get custom arrangements:
            
            Custom agreements available for:
            - Annual or multi-year contracts
            - Volume-based pricing
            - Custom SLA requirements
            - On-premise or dedicated infrastructure
            - Professional services and training
            
            Billing options:
            - Net-30, Net-60 terms available
            - Purchase orders accepted
            - Invoice billing (no credit card required)
            - ACH/wire transfer preferred
            
            Enterprise features:
            - Dedicated infrastructure and support
            - Custom integration assistance
            - White-label deployment options
            - Extended support hours (24/7)
            - Custom development requests
            
            Contact sales:
            - Schedule discovery call through dashboard
            - Email: enterprise@yourcompany.com
            - Sales responds within 24 hours
            
            No commitment to discuss options.
            Typical minimum: $500/month for custom agreements.
            """,
            metadata={
                "category": "billing",
                "topic": "enterprise_billing",
                "type": "sales"
            }
        ),
        Document(
            page_content="""
            Downgrades and Changing Plans
            
            Switching subscription tiers:
            
            Downgrading:
            - Changes take effect at end of current billing period
            - You keep full access until period ends
            - Prorated credit applied to next billing cycle
            - Setup downgrade reminder in dashboard
            
            Upgrading:
            - Immediate access to new tier features
            - Prorated charge to account balance
            - New billing cycle starts immediately
            - Previous tier's unused credits reset
            
            Switching to annual:
            - Save 20% compared to monthly
            - Charges applied immediately
            - 12-month billing cycle starts
            - Auto-renew enabled
            
            Impact on open source libraries:
            - Library access unaffected by plan changes
            - Local development continues as normal
            - Only cloud API access changes with tier
            
            Best practices:
            - Monitor usage before downgrading
            - Contact support to discuss options
            - Use usage alerts to track consumption
            
            No penalty for plan changes - adjust as your needs change.
            """,
            metadata={
                "category": "billing",
                "topic": "plan_changes",
                "type": "process"
            }
        ),
        Document(
            page_content="""
            Disputes, Chargebacks, and Billing Errors
            
            Handling billing disputes:
            
            If charged incorrectly:
            1. Review invoice in dashboard
            2. Check usage logs and transaction history
            3. Contact support with invoice number and details
            4. We investigate within 2 business days
            
            Common issues we resolve quickly:
            - Duplicate charges: Immediate refund
            - Charges for canceled accounts: Full refund
            - Credit miscalculations: Corrected immediately
            - Tax calculation errors: Adjusted and refunded
            
            Dispute process:
            - Email billing disputes to billing@yourcompany.com
            - Include account email and invoice number
            - We respond within 48 hours
            - Most disputes resolved within 5 business days
            
            Chargebacks (avoid these):
            - If you initiate a chargeback instead of contacting us
            - Your account may be suspended
            - We will provide evidence to payment processor
            - Better to contact us directly for faster resolution
            
            Our commitment:
            - We investigate all disputes fairly
            - Honest mistakes corrected immediately
            - No fees for legitimate errors on our part
            - Transparent billing and usage tracking
            
            For legal or compliance questions, contact legal@yourcompany.com
            """,
            metadata={
                "category": "billing",
                "topic": "disputes",
                "type": "policy",
                "high_risk": True
            }
        ),
    ]
    
    # Add documents to vector store
    print("Adding billing documents to vector store...")
    vector_store.add_documents(billing_docs, category="billing")
    print(f"Added {len(billing_docs)} billing documents to the knowledge base.")
    
    print("\nBilling knowledge base seeded successfully!")
    print("\nSample queries to test:")
    print("- 'What are the pricing plans and API credit limits?'")
    print("- 'How do API credits work and when do I get charged overage?'")
    print("- 'Can I use the open source libraries without a paid subscription?'")
    print("- 'How do I cancel my subscription and can I get a refund?'")
    print("- 'My payment failed - what happens to my account?'")
    print("- 'How do I add team members to my Business plan?'")
    print("- 'What's the difference between free and paid features?'")


if __name__ == "__main__":
    print("Seeding Pinecone vector database with billing knowledge base...\n")
    try:
        seed_billing_kb()
    except Exception as e:
        print(f"Error seeding database: {e}")
        print("\nMake sure you have:")
        print("1. Set PINECONE_API_KEY in your environment")
        print("2. Installed dependencies: pip install pinecone-client langchain-pinecone")
        print("3. Created a .env file with your API key")

