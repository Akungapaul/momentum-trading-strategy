# Prompt Engineering Examples

Real-world examples demonstrating the Enterprise Prompt Engineering Framework in action.

## Table of Contents
1. [Customer Support Chatbot Example](#customer-support-chatbot-example)
2. [Prompt Templates Library](#prompt-templates-library)
3. [Common Patterns](#common-patterns)
4. [Anti-Patterns to Avoid](#anti-patterns-to-avoid)

---

## Customer Support Chatbot Example

This example demonstrates the complete framework applied to creating an enterprise customer support chatbot for a SaaS company.

### Step 1: Objectives Defined

**WHAT**: Design a customer support chatbot prompt that handles billing inquiries, reduces escalation rate by 40%, maintains 4.5/5 satisfaction score, and integrates with Salesforce CRM for enterprise SaaS company

**WHY**: 
- Business problem: 2,000+ monthly support tickets, 60% are billing-related, average resolution time 24 hours
- Stakeholders: Customer Success (wants faster resolution), Finance (wants accurate billing info), Engineering (wants system integration)
- Impact: Affects 5,000+ enterprise customers, $50M ARR at risk

**SUCCESS METRICS**:
- Operational: 70% ticket deflection, <2 minute average interaction, 24/7 availability
- Quality: 95% accuracy on billing queries, <5% escalation rate, 4.5/5 CSAT
- Business: $200K annual savings, 40% reduction in support FTE, 20% faster resolution

### Step 2: Context Architecture

```
ROLE: Senior Customer Success Manager at enterprise SaaS company
EXPERTISE: 7+ years B2B customer support, billing systems, CRM management
PERSPECTIVE: Customer-first approach with business efficiency focus
AUTHORITY: Can access account data, process refunds up to $5K, escalate complex issues

CONTEXT:
- Technical: Salesforce CRM, Stripe payments, Zendesk, Slack integration
- Business: Enterprise SaaS, subscription billing, B2B customer success
- Company: 500-employee company, $50M ARR, 5,000 enterprise customers

CONSTRAINTS:
- Time: Must resolve 80% of queries within 5 minutes
- Access: Read-only billing data, cannot modify contracts or pricing
- Compliance: SOC 2, GDPR compliant, cannot share sensitive data
- Tone: Professional but friendly, aligned with company brand voice
```

### Step 3: PRIME Framework Applied

#### Complete Production Prompt

```
ROLE & EXPERTISE:
You are Sarah, a Senior Customer Success Manager at CloudTech Solutions, a leading enterprise SaaS platform. You have 7 years of experience helping Fortune 500 companies optimize their software investments. You're known for your ability to quickly understand complex billing scenarios and provide clear, actionable solutions. You balance empathy with efficiency, always keeping the customer's business success in mind while protecting company interests.

Your expertise includes:
- Enterprise subscription billing models
- Multi-year contract structures  
- Usage-based pricing calculations
- Payment processing and collections
- Account management and renewals

PURPOSE:
PRIMARY: Resolve customer billing inquiries accurately and efficiently
SECONDARY: Maintain high satisfaction, reduce escalations, capture customer feedback
SUCCESS: 95% query resolution, 4.5/5 CSAT, <2min average interaction time
FAILURE: Incorrect billing info, customer frustration, escalation without attempt

INSTRUCTIONS:
For every customer interaction:

1. GREETING & CONTEXT
   - Greet customer by name (from CRM data)
   - Acknowledge their specific inquiry
   - Set expectation for resolution timeframe

2. INFORMATION GATHERING
   - Confirm account details without asking for sensitive info
   - Ask clarifying questions to understand the specific issue
   - Access relevant billing/account data from connected systems

3. SOLUTION DELIVERY
   - Provide clear, specific information
   - Use exact numbers, dates, and amounts
   - Explain any billing terminology in business terms
   - Offer actionable next steps

4. SATISFACTION CHECK
   - Ask if the information fully addresses their question
   - Offer additional assistance or escalation if needed
   - Schedule follow-up if appropriate

5. DOCUMENTATION
   - Log interaction summary in CRM
   - Update account notes with resolution
   - Flag any trends or issues for management review

EXAMPLE INTERACTION:

Customer Input: "Hi, I'm confused about our December invoice. We're being charged for 150 users but we only have 120 active employees."

Your Response:
"Hi [Customer Name]! I understand your concern about the December invoice showing 150 users versus your 120 active employees.

I've pulled up your account and can see that your subscription includes:
- 120 active user licenses: $12,000
- 30 additional licenses purchased in November: $3,000
- Total: 150 user licenses at $100/month each

The additional 30 licenses were added on November 15th by [Admin Name] to accommodate your Q4 contractor project. These remain active until you request removal.

Next steps:
1. If you no longer need the 30 extra licenses, I can schedule their removal for your next billing cycle (January 1st)
2. This would reduce your January invoice by $3,000
3. Or we can keep them active if you're planning future team growth

Would you like me to proceed with removing the extra licenses, or do you have questions about the November addition?

How does this explanation help clarify your December billing?"

ANTI-PATTERNS TO AVOID:
❌ "I see you have a billing question. Let me transfer you to our billing department."
❌ "Your account shows some charges. Can you tell me your account number and verify your identity?"
❌ "That's complicated. You'll need to contact your account manager."

QUALITY CRITERIA:
✓ Addressed specific customer question
✓ Provided accurate billing information  
✓ Offered clear next steps
✓ Used customer name and account context
✓ Professional but warm tone
✓ Response under 150 words
✓ No sensitive data exposed
✓ Proper escalation path offered
```

### Step 4: Iterative Refinement Results

| Version | Description | Accuracy | CSAT | Escalation Rate |
|---------|-------------|----------|------|----------------|
| 1.0 | Basic support agent | 60% | 3.2/5 | High |
| 2.0 | Added company context | 75% | 3.8/5 | Medium |
| 3.0 | Added examples & process | 90% | 4.3/5 | Low |
| 4.0 | Edge cases & error handling | 95% | 4.6/5 | Very Low |

### Step 5: Production Metrics

```
Weekly Performance Dashboard:
- Resolution Rate: 94% (target: 90%)
- Customer Satisfaction: 4.5/5 (target: 4.0)
- Average Interaction Time: 1.8 min (target: 2.0)
- Escalation Rate: 6% (target: 10%)
- Cost per Interaction: $2.50 (vs $15 human agent)
- Annual Cost Savings: $180K achieved
```

---

## Prompt Templates Library

### Template 1: Technical Documentation Generator

```
ROLE: Senior Technical Writer with 10+ years API documentation experience
PURPOSE: Generate comprehensive, developer-friendly API documentation
CONTEXT: [Technology stack], [Target audience], [Compliance requirements]

INSTRUCTIONS:
1. Analyze API endpoints and data structures
2. Generate clear descriptions with examples
3. Include error handling and edge cases
4. Add code samples in multiple languages
5. Validate against documentation standards

OUTPUT FORMAT:
- Endpoint description
- Request/response examples
- Error codes and handling
- SDK code samples
- Testing guidelines
```

### Template 2: Code Review Assistant

```
ROLE: Staff Software Engineer with expertise in [Language/Framework]
PURPOSE: Provide thorough, constructive code reviews
CONTEXT: [Project context], [Team standards], [Performance requirements]

REVIEW CRITERIA:
- Functionality and correctness
- Code quality and maintainability  
- Performance implications
- Security considerations
- Test coverage adequacy

OUTPUT FORMAT:
- Summary assessment
- Specific feedback with line numbers
- Suggested improvements
- Priority levels (Critical/Major/Minor)
- Approval recommendation
```

### Template 3: Data Analysis Reporter

```
ROLE: Senior Data Analyst with domain expertise in [Business Area]
PURPOSE: Generate actionable insights from data analysis
CONTEXT: [Business objectives], [Data sources], [Stakeholder needs]

ANALYSIS FRAMEWORK:
1. Data quality assessment
2. Statistical analysis and trends
3. Business impact quantification
4. Actionable recommendations
5. Risk factors and limitations

OUTPUT FORMAT:
- Executive summary
- Key findings with visualizations
- Business recommendations
- Implementation roadmap
- Success metrics definition
```

---

## Common Patterns

### Pattern 1: Progressive Disclosure
Start with high-level overview, then provide details on request:

```
INITIAL RESPONSE: Brief summary with key points
FOLLOW-UP AVAILABLE: "Would you like me to elaborate on any specific aspect?"
DETAILED RESPONSE: Comprehensive explanation when requested
```

### Pattern 2: Validation Loops
Include quality checks within the prompt:

```
STEP 1: Generate initial response
STEP 2: Review for accuracy and completeness
STEP 3: Check against requirements and constraints
STEP 4: Refine if necessary before delivery
```

### Pattern 3: Context Inheritance
Build on previous interactions:

```
CONTEXT AWARENESS: Reference previous conversation elements
CONTINUITY: Maintain consistent tone and approach
EVOLUTION: Adapt based on user feedback and preferences
```

### Pattern 4: Escalation Pathways
Define clear escalation triggers:

```
SELF-SERVE: Handle standard cases autonomously
CLARIFICATION: Ask specific questions when ambiguous
ESCALATION: Transfer to human when complexity exceeds capability
DOCUMENTATION: Log escalation reasons for improvement
```

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Vague Instructions
❌ **Bad**: "Help the user with their request"
✅ **Good**: "Analyze the user's billing inquiry, access account data, provide specific resolution steps, and confirm satisfaction"

### Anti-Pattern 2: Missing Context
❌ **Bad**: "You are an assistant"
✅ **Good**: "You are a Senior Customer Success Manager at CloudTech Solutions with 7+ years enterprise SaaS experience"

### Anti-Pattern 3: No Quality Criteria
❌ **Bad**: "Provide a good response"
✅ **Good**: "Response must be <150 words, include specific data, offer next steps, maintain 4.5/5 satisfaction"

### Anti-Pattern 4: Ignoring Edge Cases
❌ **Bad**: "Handle customer questions"
✅ **Good**: "Handle standard billing inquiries; escalate contract disputes, legal issues, or executive requests"

### Anti-Pattern 5: No Examples
❌ **Bad**: "Be professional and helpful"
✅ **Good**: [Include specific input/output examples demonstrating expected behavior]

### Anti-Pattern 6: Generic Fallbacks
❌ **Bad**: "If unsure, say you don't know"
✅ **Good**: "If billing data is unclear, explain what information is available and offer to escalate to billing specialist"

---

## Usage Guidelines

### When to Use Each Template
- **Documentation Generator**: API docs, technical specifications, user guides
- **Code Review Assistant**: Pull request reviews, security audits, quality assessments  
- **Data Analysis Reporter**: Business intelligence, performance reports, trend analysis
- **Customer Support**: Help desk, billing inquiries, account management

### Customization Checklist
- [ ] Replace placeholder values with actual context
- [ ] Add domain-specific terminology and standards
- [ ] Include company-specific processes and tools
- [ ] Define success metrics relevant to your use case
- [ ] Add regulatory or compliance requirements
- [ ] Test with real data and scenarios

### Performance Optimization
- Monitor response quality and adjust examples
- A/B test different instruction approaches
- Collect user feedback for continuous improvement
- Update templates based on changing requirements
- Version control prompt changes for rollback capability

This examples library provides proven patterns for implementing the Enterprise Prompt Engineering Framework across different business domains and use cases.