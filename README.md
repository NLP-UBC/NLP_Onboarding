# UBC NLP Group Onboarding Document
Welcome to the UBC NLP Group! We are glad to have a new talent joining us. This is a tutorial that will help you quickly onboard to the group and obtain access to compute.

## Get in Contact
Our group uses [Slack](https://slack.com/) for communications. Please download Slack and ask your supervisor or other students to add you to the group.
- [Students in the lab rooms](https://docs.google.com/spreadsheets/d/1zToD0kpiL6H8AaXDN_-XSXsLJ-tUinK5UKFc2Qvolc8/edit?gid=0#gid=0): please fill yourself in.
- CS building logistics: [Vivian Leung](vivian.leung@ubc.ca) and [Patrick Lai](plai@cs.ubc.ca), please email them for lost monitors, etc.

## Keeping Your Monitor Safe
We have had instances monitors/keyboard/mouse disappearing from your desk a few times. Mostly because students from NLP and HCI share the lab rooms, and they sometimes mess up the seating & move things around. When this happens, first check in the lab room whether your equipments are moved to some other desk and ask in the Slack channels. If not, email Vivian or Patrick. To prevent this from happening, I recommend writing a note to indicate that your desk is in use and keep that note on your desk.

## Compute Access
There are three sources of compute available for all members: [Compute Canada](compute/Compute_Canada.md), UBC's [ARC Sockeye](compute/ARC_Sockeye.md) and the [NLP Group Compute Servers](compute/NLP_Servers.md). Depending on your supervisor, you may have other compute resources available to you. Detailed instructions to get access for these resources as well as a simple tutorial are provided in the above links. The goal of this documentation is for you to obtain access to these compute resources and learn basic usage of these resources. For more technical documentations, you may wish to consult the technical documentation of each cluster instead.

## Supervisor-specific Onboarding Instructions
Depending on your supervisor, there may be different onboarding instructions. These instructions are under [supervisor](supervisor/).

## API Security
You may be granted funds/credits to LLM APIs like OpenAI or Gemini. However, it is important to keep in mind that API keys of any kind must be stored on local machines, not on GitHub or any other service provider devices, not even if they promise you "privacy" (i.e. private repo), to avoid the key being stolen. It is also a good practice to constantly observe the usage of the API to make sure that no uncommon charges are present.  
Most importantly, if you spot any unexpected charges, do not panic. Delete/Deactivate your API key immediately and report to your supervisor.  
Take a look at [Using APIs](./technical/using_APIs.md), you may find that useful.

## Quick Links for More Advanced Technical Stuff
- [Printing](https://my.cs.ubc.ca/docs/how-print) (closest printers to our lab: X409 and X452)