"""
Canonical profile values derived from Seraj's resume/profile.

Keep resume-driven details in one place so the search config, form answers,
and matching logic stay in sync.
"""

DEFAULT_RESUME_PATH = "Seraj_Khan___Senior_Software_Engineer.pdf"

FIRST_NAME = "Seraj"
MIDDLE_NAME = ""
LAST_NAME = "Khan"
PHONE_NUMBER = "8229020370"
EMAIL = "serajkhan48522@gmail.com"
LINKEDIN_URL = "https://www.linkedin.com/in/its-seraj/"
GITHUB_URL = "https://github.com/its-seraj"

# Keep location values broad and safe for most job forms.
CURRENT_CITY = "Bengaluru"
STREET = "Mahadevpura"
STATE = "Karnataka"
ZIPCODE = "560048"
COUNTRY = "India"

# Keep a machine-friendly numeric version plus a resume-style display version.
YEARS_OF_EXPERIENCE = "4"
CURRENT_EXPERIENCE = 6
RECENT_EMPLOYER = "BambooBox"

SEARCH_LOCATION = "India"

SEARCH_TERMS = [
    "Senior Software Engineer",
    "Software Engineer",
    "AI Engineer",
    "Forward Deployed Engineer",
    "Forward Deployed Software Engineer",
    "AI Software Engineer",
    "Generative AI Engineer",
    "LLM Engineer",
    "Full Stack AI Engineer",
    "AI Solutions Engineer",
    "Backend Engineer",
    "Backend Developer",
    "Software Developer",
    "Software Development Engineer",
    "Full Stack Developer",
    "Fullstack Developer",
    "Node.js Developer",
    "Platform Engineer",
    "API Engineer",
]

ALLOWED_JOB_TITLES = [
    "Node.js",
    "Node js",
    "NodeJS",
    "React.js",
    "React js",
    "JavaScript",
    "TypeScript",
    "MongoDB",
    "PostgreSQL",
    "Redis",
    "Microservices",
    "Backend Engineer",
    "Backend Developer",
    "Software Engineer",
    "Software Developer",
    "Software Development Engineer",
    "SDE",
    "Senior Software Engineer",
    "Senior Backend Engineer",
    "Platform Engineer",
    "API Engineer",
    "Fullstack Developer",
    "Full Stack Developer",
    "AI Engineer",
    "AI Developer",
    "AI Software Engineer",
    "Forward Deployed Engineer",
    "Forward Deployed Software Engineer",
    "Forward Deployed",
    "Generative AI Engineer",
    "GenAI Engineer",
    "LLM Engineer",
    "Full Stack AI Engineer",
    "AI Solutions Engineer",
    "Founding Engineer",
    "Founding AI Engineer",
    "AI Application Engineer",
    "Machine Learning Engineer",
    "ML Engineer",
    "Applied AI Engineer",
]

GENERIC_ENGINEERING_TITLES = [
    "backend engineer",
    "backend developer",
    "node.js developer",
    "node js developer",
    "node backend engineer",
    "software engineer",
    "software developer",
    "software development engineer",
    "sde",
    "platform engineer",
    "api engineer",
    "fullstack developer",
    "full stack developer",
    "ai engineer",
    "ai developer",
    "ai software engineer",
    "forward deployed engineer",
    "forward deployed software engineer",
    "forward deployed",
    "generative ai engineer",
    "genai engineer",
    "llm engineer",
    "full stack ai engineer",
    "ai solutions engineer",
    "founding engineer",
    "founding ai engineer",
    "applied ai engineer",
    "machine learning engineer",
    "ml engineer",
]

# Keep these if you want to avoid pushing very senior roles or junior/associate/intern roles.
SENIORITY_BLACKLIST = [
    "staff",
    "principal",
    "manager",
    "director",
    "head of",
    "architect",
    "junior",
    "jr",
    "jr.",
    "associate",
    "intern",
    "internship",
    "trainee",
    "entry level",
    "entry-level",
    "fresher",
    "graduate",
]

ROLE_FAMILY_KEYWORDS = [
    "backend",
    "fullstack",
    "node.js",
    "node js",
    "javascript",
    "typescript",
    "api",
    "microservices",
    "llm",
    "ai",
    "software engineer",
    "platform",
    "crm",
    "ads",
    "forward deployed",
    "forward deployment",
    "generative ai",
    "genai",
    "agentic",
    "agents",
    "rag",
    "langchain",
    "llamaindex",
]

STRONG_MATCH_KEYWORDS = [
    "javascript",
    "typescript",
    "node js",
    "node.js",
    "react js",
    "react",
    "mongodb",
    "postgresql",
    "redis",
    "microservices",
    "rest api",
    "api integration",
    "langchain",
    "gpt-4o",
    "llm",
    "ai integration",
    "docker",
    "kubernetes",
    "aws",
    "jwt",
    "rbac",
    "genai",
    "generative ai",
    "llamaindex",
    "vector database",
    "vector db",
    "pgvector",
    "embeddings",
    "agents",
    "agentic",
    "prompt engineering",
    "forward deployed",
]

SUPPORTING_MATCH_KEYWORDS = [
    "express",
    "nestjs",
    "next.js",
    "supabase",
    "nginx",
    "ec2",
    "vercel",
    "crm",
    "ad platform",
    "apollo",
    "lead scoring",
    "workflow automation",
    "distributed systems",
    "git",
    "github",
    "prompt engineering",
    "rag",
    "postgres",
    "caching",
    "performance optimization",
    "third-party integration",
    "solutions engineering",
    "client facing",
    "customer facing",
    "enterprise ai",
    "fine-tuning",
]

LINKEDIN_HEADLINE = (
    "Senior Software Engineer | Backend Engineer | Node.js | "
    "Microservices | AI/LLM Integrations"
)

LINKEDIN_SUMMARY = """
Senior Software Engineer with 3.5+ years of experience building scalable
backend systems and full-stack products using Node.js, JavaScript,
TypeScript, PostgreSQL, MongoDB, Redis, and microservices. I have worked on
CRM and ad-platform integrations, performance-focused backend architecture,
and AI/LLM integrations using LangChain and GPT models. I am targeting
backend, full-stack, and platform engineering roles where strong product
thinking and production ownership matter.
""".strip()

COVER_LETTER = """
Dear Hiring Team,

I am a Senior Software Engineer with 3.5+ years of experience building
production backend systems and full-stack products using Node.js,
PostgreSQL, MongoDB, Redis, and microservices. My recent work has included
backend architecture, CRM and ad-platform integrations, performance
optimization, and AI/LLM-powered workflows using LangChain and GPT models.

My background fits roles that require strong backend engineering, API design,
integration-heavy product development, and ownership of scalable systems. I
would be glad to contribute across system design, implementation, and
production delivery.

Regards,
Seraj Khan
""".strip()

RESUME_TEXT_FOR_MATCHING = """
Seraj Khan

Professional Summary:
Senior Software Engineer with 3.5+ years of experience building scalable
backend systems and full-stack applications. Strong background in Node.js,
JavaScript, TypeScript, PostgreSQL, MongoDB, Redis, microservices,
third-party integrations, and AI/LLM-enabled product features.

Professional Experience:
- BambooBox, Senior Software Engineer. Led backend architecture and built
  scalable APIs, data workflows, CRM/ad-platform integrations, and
  performance improvements across production systems.
- Prior startup experience building full-stack applications and backend
  services using the JavaScript ecosystem.

Projects:
- Trend Sniper: market/news sentiment and sector-labeling pipeline using a
  Node.js backend, PostgreSQL/Supabase, and an ML microservice hosted on
  Hugging Face.
- Lead enrichment and scoring workflows integrating LinkedIn ads activity,
  Apollo enrichment, and client delivery pipelines.
- Postman clone using MongoDB.

Skills:
Node.js, JavaScript, TypeScript, Express.js, React, MongoDB, PostgreSQL,
Redis, REST APIs, Microservices, LangChain, GPT-4o, AI/LLM integrations,
Docker, Kubernetes, AWS EC2, Nginx, Vercel, Git, GitHub.
""".strip()

USER_INFORMATION_ALL = f"""
Name: Seraj Khan
Phone: +91-{PHONE_NUMBER}
Email: {EMAIL}
LinkedIn: {LINKEDIN_URL}
Location: {CURRENT_CITY}, {STATE}, {COUNTRY}

Target roles: Senior Software Engineer, Backend Engineer, Full Stack
Developer, Platform Engineer, Software Engineer

Professional summary:
{LINKEDIN_SUMMARY}

Experience:
- Senior Software Engineer at {RECENT_EMPLOYER}
- Total professional experience: {YEARS_OF_EXPERIENCE} years
- Notice Period: 30 days (1 month, flexible)
- Current CTC: 11,00,000 INR (11 LPA)
- Expected CTC: 18,00,000 INR (18 LPA)
- Work authorization: Legally authorized to work in India without sponsorship

Key work:
- Built backend systems and microservices using Node.js, PostgreSQL,
  MongoDB, and Redis
- Worked on CRM and ad-platform integrations with production business impact
- Designed AI/LLM-powered workflows using LangChain and GPT models
- Improved API performance and backend architecture for scalable products
- Built and deployed services on AWS EC2 with Nginx, Vercel, and modern dev
  tooling

Technical skills:
- Languages: JavaScript, TypeScript
- Backend: Node.js, Express.js, REST APIs, Microservices, JWT, RBAC
- Frontend: React
- Databases: PostgreSQL, MongoDB, Redis, Supabase
- AI/LLM: LangChain, GPT-4o, RAG-style workflows, prompt engineering
- Infra/DevOps: Docker, Kubernetes, AWS EC2, Nginx, Vercel, GitHub

Projects:
- LinkedIn ads and Apollo enrichment workflow
- CRM and MAP platform integrations
- Trend Sniper

Education:
- B.Tech in Computer Science Engineering
""".strip()
