BINARYBOT — ROLE AND PERMISSION MATRIX SPECIFICATION

Version: 1.0
Status: CANONICAL
Location: /opt/binarybot/docs/ROLE_AND_PERMISSION_MATRIX_SPEC.md


------------------------------------------------------------
1. PURPOSE
------------------------------------------------------------

This document defines the canonical role hierarchy and permission
matrix for the BinaryBot operational system.

The role system governs:

• who can access the control panel  
• who can modify strategy parameters  
• who can view diagnostics and research  
• who can manage signal distribution  
• who can manage users and affiliates  

This document must remain consistent with:

CONTROL_PANEL_HIERARCHY_AND_INTELLIGENCE_SPEC.md  
ADMIN_CONTROL_SPEC.md  
ADMIN_OPERATIONS_SPEC.md  
SECURITY_MODEL.md  

The role system ensures that operational power is distributed
correctly while protecting critical system components.


------------------------------------------------------------
2. ROLE HIERARCHY
------------------------------------------------------------

BinaryBot uses a strict hierarchical role model.

Roles are ordered by authority level:

OWNER
↓
PRIMARY_ADMIN
↓
FUNCTIONAL_ADMIN
↓
ANALYST
↓
MODERATOR
↓
AFFILIATE_ADMIN
↓
USER


------------------------------------------------------------
3. ROLE DEFINITIONS
------------------------------------------------------------


OWNER
------------------------------------------------------------

The owner is the supreme authority of the system.

Responsibilities:

• system strategy oversight  
• final authority on parameter changes  
• research interpretation  
• architecture direction  
• admin supervision  

Capabilities:

• full control of strategy parameters  
• full control of symbol lists  
• full control of distribution tiers  
• full access to research and intelligence reports  
• full access to audit logs  
• full access to affiliate system  
• ability to promote/demote admins  

The OWNER role cannot be overridden by any other role.



PRIMARY_ADMIN
------------------------------------------------------------

The primary admin is the operational controller of the system.

Responsibilities:

• daily system operation  
• supervising functional admins  
• monitoring signals and diagnostics  
• managing channel behavior  

Capabilities:

• change strategy thresholds  
• change symbol watchlist  
• manage channel limits  
• run diagnostics  
• view research reports  
• manage functional admins  

Restrictions:

• cannot override OWNER-level restrictions
• cannot modify governance rules



FUNCTIONAL_ADMIN
------------------------------------------------------------

Functional admins are specialists responsible for specific areas.

Typical functional admin categories:

• Strategy admin  
• Distribution admin  
• Monitoring admin  
• Research admin  

Capabilities depend on specialization.

Example permissions:

Strategy Admin

• adjust score thresholds  
• adjust SR buffer  
• adjust spike filter  

Distribution Admin

• manage Telegram channels  
• manage signal routing  

Monitoring Admin

• view engine diagnostics  
• view health metrics  

Research Admin

• access strategy intelligence reports  
• generate auditor reports  

Restrictions:

• cannot change global governance
• cannot modify role hierarchy



ANALYST
------------------------------------------------------------

Analysts study strategy performance and produce reports.

Responsibilities:

• analyze strategy behavior  
• interpret auditor reports  
• produce insights for the owner  

Capabilities:

• view AI strategy auditor reports  
• view observability logs  
• run analysis scripts  

Restrictions:

• cannot modify system configuration
• cannot modify parameters
• cannot publish signals



MODERATOR
------------------------------------------------------------

Moderators manage community and channel environment.

Responsibilities:

• community moderation  
• user management in channels  

Capabilities:

• moderate Telegram groups  
• manage community discussions  

Restrictions:

• cannot modify signals
• cannot access strategy internals
• cannot view audit internals



AFFILIATE_ADMIN
------------------------------------------------------------

Affiliate admins represent influencers or partners who bring users
to the signal ecosystem.

Responsibilities:

• promote signal channels  
• onboard users  

Capabilities:

• view statistics for their referred users  
• view subscriber counts  
• view commission statistics  

Affiliate admins may see:

• number of users they referred  
• subscription conversions  
• earnings from referral program  

Restrictions:

• cannot view strategy internals
• cannot access diagnostics
• cannot access research
• cannot access admin tools



USER
------------------------------------------------------------

Users are the subscribers of signal channels.

Capabilities:

• receive signals  
• view signals in Telegram  

Restrictions:

• no administrative privileges
• no internal system visibility



------------------------------------------------------------
4. PERMISSION MATRIX
------------------------------------------------------------

Permission categories:

Strategy Control  
Distribution Control  
Diagnostics Access  
Research Access  
Affiliate Data  
User Management  
Role Management  


Permission Table:

ROLE            Strategy  Distribution  Diagnostics  Research  Affiliate  User Mgmt  Role Mgmt
-----------------------------------------------------------------------------------------------
OWNER           YES       YES           YES          YES       YES        YES        YES
PRIMARY_ADMIN   YES       YES           YES          YES       YES        YES        NO
FUNCTIONAL_ADMIN LIMITED  LIMITED       YES          LIMITED   NO         YES        NO
ANALYST         NO        NO            YES          YES       NO         NO         NO
MODERATOR       NO        NO            NO           NO        NO         YES        NO
AFFILIATE_ADMIN NO        NO            NO           NO        YES        NO         NO
USER            NO        NO            NO           NO        NO         NO         NO



------------------------------------------------------------
5. PERMISSION DOMAINS
------------------------------------------------------------

Permissions are grouped into domains.

Domains:

STRATEGY_DOMAIN
DISTRIBUTION_DOMAIN
OBSERVABILITY_DOMAIN
INTELLIGENCE_DOMAIN
COMMUNITY_DOMAIN
AFFILIATE_DOMAIN
SECURITY_DOMAIN


Example:

Strategy parameters belong to:

STRATEGY_DOMAIN

Signal publishing belongs to:

DISTRIBUTION_DOMAIN

Strategy diagnostics belong to:

INTELLIGENCE_DOMAIN



------------------------------------------------------------
6. ROLE STORAGE MODEL
------------------------------------------------------------

Roles must be stored in persistent configuration.

Recommended location:

/opt/binarybot/config/roles.json

Example:

{
  "owner": [12345678],
  "primary_admin": [23456789],
  "functional_admin": {
      "strategy": [34567890],
      "distribution": [],
      "monitoring": []
  },
  "analyst": [],
  "moderator": [],
  "affiliate_admin": {}
}


Affiliate admins must include metadata:

{
  "affiliate_admin": {
      "influencer_1": {
          "telegram_id": 12345,
          "referral_code": "TRADER_X"
      }
  }
}



------------------------------------------------------------
7. ADMIN COMMAND PERMISSION CHECK
------------------------------------------------------------

Every admin command must check role authorization.

Example flow:

1. Telegram message received
2. user_id extracted
3. role lookup executed
4. permission verified
5. command allowed or rejected

Example rejection:

Unauthorized command attempt.


------------------------------------------------------------
8. SECURITY RULES
------------------------------------------------------------

Critical rules:

1. Owner privileges cannot be delegated automatically.

2. Strategy modification commands must be logged.

3. All admin actions must generate observability logs.

Example log event:

admin_action

Fields:

timestamp  
admin_id  
role  
action  
parameters  
result



------------------------------------------------------------
9. FUTURE ROLE EXTENSIONS
------------------------------------------------------------

Future roles may include:

• AI Research Operator  
• Risk Manager  
• Affiliate Manager  

These roles must be integrated into the permission matrix
before implementation.


------------------------------------------------------------
10. FINAL STATEMENT
------------------------------------------------------------

The role and permission matrix ensures that BinaryBot remains:

• secure
• auditable
• scalable
• manageable

As the system grows to include:

• AI intelligence layers
• affiliate ecosystems
• large user bases

strict role separation becomes essential to operational stability.