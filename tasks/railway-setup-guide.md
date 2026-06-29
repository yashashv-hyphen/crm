# Step-by-Step: Deploy CRM for Free

## What You're Setting Up

| Service | What it does | Cost |
|---------|-------------|------|
| Railway | Hosts backend + Celery + PostgreSQL + Redis | Free ($5/mo credit) |
| Cloudflare R2 | Stores uploaded Excel files | Free (10GB) |
| Brevo | Sends OTP + welcome emails | Free (300/day) |

---

## Step 1: Create Free Accounts (5 min)

1. **Railway** → go to https://railway.app → click "Login" → sign in with GitHub
   - If you don't have GitHub, create one first at https://github.com

2. **Cloudflare** → go to https://cloudflare.com → sign up (free)

3. **Brevo** → go to https://brevo.com → sign up (free)

---

## Step 2: Push Code to GitHub (5 min)

1. Go to https://github.com/new → create a **private** repository named `crm`
2. Run these commands in your terminal inside `/home/venom/CRM`:

```bash
git init
git add .
git commit -m "Initial CRM deploy"
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/crm.git
git push -u origin main
```

---

## Step 3: Set Up Cloudflare R2 (5 min)

1. Log into Cloudflare → click **R2** in the left sidebar
2. Click **Create bucket** → name it `crm-uploads` → Create
3. Click **Manage R2 API Tokens** → Create API Token
   - Permissions: **Object Read & Write**
   - Apply to bucket: `crm-uploads`
   - Click **Create API Token**
4. **Copy and save** these values (you'll need them later):
   - Access Key ID
   - Secret Access Key
   - Endpoint URL (looks like: `https://abc123.r2.cloudflarestorage.com`)

---

## Step 4: Set Up Brevo SMTP (3 min)

1. Log into Brevo → click your name (top right) → **SMTP & API**
2. Click **SMTP** tab → note the SMTP settings:
   - Host: `smtp-relay.brevo.com`
   - Port: `587`
3. Click **Generate a new SMTP key** → copy the password shown

Save these:
- SMTP login: your Brevo account email
- SMTP password: the key you just generated

---

## Step 5: Create Railway Project (10 min)

1. Go to https://railway.app/new → click **Deploy from GitHub repo**
2. Select your `crm` repo
3. Railway will detect it — **don't deploy yet**, click **Add variables** first

### Add PostgreSQL

4. In your project dashboard → click **+ New** → **Database** → **PostgreSQL**
5. Once provisioned, click the PostgreSQL service → **Variables** tab
6. Copy the `DATABASE_URL` value (starts with `postgresql://...`)

### Add Redis

7. Click **+ New** → **Database** → **Redis**
8. Copy the `REDIS_URL` value (starts with `redis://...`)

---

## Step 6: Set Environment Variables in Railway (5 min)

Click your **backend** service → **Variables** tab → add each of these:

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | (paste from PostgreSQL — change `postgresql://` to `postgresql+asyncpg://`) |
| `REDIS_URL` | (paste from Redis) |
| `SECRET_KEY` | (generate one: run `python3 -c "import secrets; print(secrets.token_hex(32))"` in terminal) |
| `R2_ACCESS_KEY_ID` | (from Step 3) |
| `R2_SECRET_ACCESS_KEY` | (from Step 3) |
| `R2_ENDPOINT_URL` | (from Step 3, e.g. `https://abc123.r2.cloudflarestorage.com`) |
| `R2_BUCKET` | `crm-uploads` |
| `SMTP_USER` | (your Brevo email address) |
| `SMTP_PASSWORD` | (SMTP key from Step 4) |
| `FROM_EMAIL` | `noreply@newtrendscommerce.in` |
| `ALLOWED_EMAIL_DOMAIN` | `newtrendscommerce.in` |
| `ALLOWED_ORIGINS` | (leave blank for now, fill in after first deploy) |
| `ENVIRONMENT` | `production` |
| `SECURE_COOKIES` | `true` |

**For the celery-worker service**, add these same variables (copy from backend service).

---

## Step 7: Run Database Migrations (2 min)

In your local terminal, inside `/home/venom/CRM/backend`:

```bash
DATABASE_URL="postgresql+asyncpg://YOUR_RAILWAY_DB_URL" alembic upgrade head
```

Replace `YOUR_RAILWAY_DB_URL` with the PostgreSQL URL from Railway (replace `postgresql://` with `postgresql+asyncpg://`).

---

## Step 8: Deploy

1. Railway auto-deploys when you push to GitHub
2. Watch the **Deployments** tab — build takes ~3-5 min
3. Once deployed, click **Settings** → copy your public URL (e.g. `https://crm-backend-xxx.up.railway.app`)

---

## Step 9: Update ALLOWED_ORIGINS

1. Go back to Railway → backend service → Variables
2. Set `ALLOWED_ORIGINS` = `https://crm-backend-xxx.up.railway.app` (your URL from Step 8)
3. Railway will redeploy automatically

---

## Step 10: Create Your First Admin User

Run this locally (one time only):

```bash
cd /home/venom/CRM/backend
DATABASE_URL="postgresql+asyncpg://YOUR_RAILWAY_DB_URL" python seed_admin.py
```

---

## Step 11: Test

Open your Railway URL in a browser — you should see the CRM login page.

---

## Optional: Custom Domain

In Railway → backend service → **Settings** → **Domains** → Add custom domain → enter `crm.ntcplai.com`

Then update your DNS:
- Add a `CNAME` record: `crm` → `(Railway-provided value)`
- SSL is automatic (Let's Encrypt via Railway)
