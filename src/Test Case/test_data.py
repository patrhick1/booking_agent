
#!/usr/bin/env python3
"""
Sample test data for the booking agent pipeline.
Contains various email scenarios to test different classification paths and behaviors.
"""

# Sample data for different email scenarios
SAMPLE_EMAILS = [
    {
        "name": "Topic-based rejection",
        "email_text": """Hi Aidrian,

Heard great things on Tom Elliot. But the podcast is about CI/CD pipelines, I'm not sure if he fits.

Best,
Grant""",
        "subject": "Re: Great episode on digital transformation",
        "sender_name": "Grant Bliphless",
        "sender_email": "assistant@sample.com"
    },
    {
        "name": "Identity-based rejection",
        "email_text": """Hello,

Thank you for reaching out about Tom Elliott appearing on our show.

Unfortunately, we only feature female entrepreneurs on our podcast as part of our mission to amplify women's voices in business.

Best regards,
Sarah Wilson""",
        "subject": "Re: Podcast Guest Opportunity - Tom Elliott",
        "sender_name": "Sarah Wilson",
        "sender_email": "sarah@sample.com"
    },
    {
        "name": "Qualification-based rejection", 
        "email_text": """Hi there,

Thanks for the pitch about Tom Elliott.

While his background sounds interesting, we typically only feature guests who have built companies with $100M+ in revenue or have had successful exits. From what I can see, his experience doesn't quite meet that threshold.

Let me know if you have other guests who might be a better fit.

Best,
Michael""",
        "subject": "Re: Tom Elliott - Podcast Guest Proposal",
        "sender_name": "Michael Chen",
        "sender_email": "michael@sample.com"
    },
    {
        "name": "Interest and booking request",
        "email_text": """Hi Aidrian,

This sounds fantastic! Tom Elliott would be perfect for our show. 

We're looking at dates in the next 2-3 weeks. Could he do Tuesday, March 15th at 2 PM EST? The interview would be about 45 minutes.

Please let me know his availability and any technical requirements.

Best,
Jennifer""",
        "subject": "Re: Tom Elliott - Perfect for Tech Leaders Podcast",
        "sender_name": "Jennifer Martinez",
        "sender_email": "jennifer@sample.com"
    },
    {
        "name": "Request for more information",
        "email_text": """Hello,

Thank you for reaching out about Tom Elliott.

Before we proceed, could you provide:
- His detailed bio and key talking points
- 2-3 sample interview questions he could answer
- Links to any previous podcast appearances
- His availability in April

This will help us determine if he's the right fit for our audience.

Thanks,
David""",
        "subject": "Re: Guest Proposal - Tom Elliott",
        "sender_name": "David Thompson",
        "sender_email": "david@sample.com"
    },
    {
        "name": "Scheduling and logistics",
        "email_text": """Hi,

Yes, we'd love to have Tom on the show! 

A few logistics questions:
- Is he available for a pre-interview call next week?
- Does he prefer morning or afternoon recordings?
- Any topics he specifically wants to avoid?
- Should we send the questions in advance?

Our target recording date is April 10th. Let me know if that works.

Best,
Lisa""",
        "subject": "Re: Tom Elliott Interview - Let's Schedule",
        "sender_name": "Lisa Roberts",
        "sender_email": "lisa@sample.com"
    },
    {
        "name": "Polite decline with future interest",
        "email_text": """Hi Aidrian,

Thanks for thinking of our podcast for Tom Elliott.

We're currently booked through the end of Q2, but his profile looks interesting for our fall season. Could we revisit this conversation in August?

Feel free to reach out then with his updated availability.

Best regards,
Alex""",
        "subject": "Re: Tom Elliott - Podcast Opportunity",
        "sender_name": "Alex Johnson",
        "sender_email": "alex@sample.com"
    },
    {
        "name": "Budget and compensation inquiry",
        "email_text": """Hello,

Tom Elliott sounds like he could be a great fit for our show.

Quick question - what are his speaking fees for podcast appearances? We have a modest budget for high-profile guests.

Also, would he be open to promoting the episode on his social channels?

Thanks,
Rachel""",
        "subject": "Re: Tom Elliott Guest Proposal - Budget Question",
        "sender_name": "Rachel Green",
        "sender_email": "rachel@sample.com"
    },
    {
        "name": "Technical requirements and format questions",
        "email_text": """Hi,

We're interested in having Tom on the podcast.

A few technical questions:
- Can he record remotely via Riverside.fm?
- Is he comfortable with video recording?
- Any preferred interview format (conversational vs structured)?
- Does he have professional audio equipment?

Our show focuses on 30-minute deep dives into specific business challenges.

Best,
Mark""",
        "subject": "Re: Tom Elliott - Technical Setup Questions",
        "sender_name": "Mark Davis",
        "sender_email": "mark@sample.com"
    },
    {
        "name": "Out of office/automated response",
        "email_text": """Thank you for your email.

I am currently out of the office until March 20th with limited email access.

If this is urgent, please contact my assistant Jane at jane@successstoriespod.com.

I will respond to your message upon my return.

Best regards,
Susan Parker
Host, Success Stories Podcast""",
        "subject": "Out of Office Auto-Reply",
        "sender_name": "Susan Parker",
        "sender_email": "susan@sample.com"
    }
]
