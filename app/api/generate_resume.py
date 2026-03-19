import asyncio
import json
import re
import time
from typing import Any, Dict, List, Optional, Sequence, Set

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.genai_integration import model
from app.services.supabase_client import get_supabase_client


router = APIRouter(prefix="/api", tags=["Resume Generation"])


ARSENAL_TABLES: Sequence[str] = (
    "personal_details",
    "professional_summary",
    "career_objectives",
    "professional_experience",
    "education",
    "projects",
    "skills",
)


class GenerateResumeRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    job_description: str = Field(..., min_length=20)
    experience_level: str = Field(default="Mid Level")
    category: str = Field(..., min_length=1)
    sub_category: str = Field(..., min_length=1)
    single_page_only: bool = Field(default=False)


def _normalize_token(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9\+\#\.\-_/ ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _unique_preserve_order(items: Sequence[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for x in items:
        nx = _normalize_token(x)
        if not nx or nx in seen:
            continue
        seen.add(nx)
        out.append(x.strip())
    return out


async def fetch_user_arsenal(user_id: str) -> Dict[str, List[Dict[str, Any]]]:
    supabase = get_supabase_client()
    print("fetch user arsenal: ", user_id)

    async def _fetch_table(table: str) -> List[Dict[str, Any]]:
        def _do() -> List[Dict[str, Any]]:
            res = supabase.table(table).select("*").eq("user_id", user_id).execute()
            data = getattr(res, "data", None)
            return data or []

        return await asyncio.to_thread(_do)

    results = await asyncio.gather(*[_fetch_table(t) for t in ARSENAL_TABLES])
    print("results: ", results)
    return {t: results[i] for i, t in enumerate(ARSENAL_TABLES)}


async def extract_keywords(job_description: str) -> List[str]:
    """
    First version: ask Gemini for a compact keyword list (skills/tools/roles).
    Falls back to simple regex token extraction if LLM output is invalid.
    """
    prompt = (
        "Extract the most important resume keywords from the job description.\n"
        "Return ONLY valid JSON in this shape:\n"
        '{ "keywords": ["...", "..."] }\n'
        "Rules:\n"
        "- Include skills, tools, technologies, role titles, frameworks, and domain keywords\n"
        "- 15 to 40 items\n"
        "- Short phrases allowed (e.g., 'machine learning', 'REST APIs')\n"
        "- No explanations, only JSON\n\n"
        "JOB DESCRIPTION:\n"
        f"{job_description}"
    )

    def _invoke() -> str:
        return str(model.invoke(prompt).content)

    raw = await asyncio.to_thread(_invoke)
    try:
        data = json.loads(raw)
        kws = data.get("keywords", [])
        if not isinstance(kws, list):
            raise ValueError("keywords not a list")
        kws = [str(x) for x in kws]
        return _unique_preserve_order(kws)
    except Exception:
        # Fallback: naive extraction
        text = _normalize_token(job_description)
        tokens = re.findall(r"[a-z0-9\+\#\.\-_/]{2,}", text)
        stop = {
            "and", "or", "the", "a", "an", "to", "of", "in", "for", "with", "on", "at",
            "is", "are", "be", "as", "by", "from", "this", "that", "you", "your",
            "we", "our", "will", "can", "must", "have", "has", "had",
            "experience", "years", "year", "responsibilities", "requirements",
        }
        tokens = [t for t in tokens if t not in stop]
        return _unique_preserve_order(tokens[:40])


def _row_text(row: Dict[str, Any], preferred_fields: Sequence[str]) -> str:
    parts: List[str] = []
    for f in preferred_fields:
        v = row.get(f)
        if isinstance(v, str) and v.strip():
            parts.append(v.strip())
    if parts:
        return " | ".join(parts)
    # fallback: stringify small subset
    for k, v in row.items():
        if isinstance(v, str) and v.strip():
            parts.append(v.strip())
        if len(parts) >= 4:
            break
    return " | ".join(parts)


def _keyword_hit_score(text: str, keywords: Sequence[str]) -> int:
    nt = _normalize_token(text)
    score = 0
    for kw in keywords:
        nkw = _normalize_token(kw)
        if not nkw:
            continue
        # simple substring match for v1
        if nkw in nt:
            score += 1
    return score


def filter_projects(projects: List[Dict[str, Any]], keywords: Sequence[str], limit: int = 5) -> List[Dict[str, Any]]:
    scored: List[tuple[int, Dict[str, Any]]] = []
    for p in projects:
        # Supabase schema: project_name, project_description, tech_stack (array)
        text = _row_text(p, ("project_name", "project_description", "tech_stack", "github_url", "project_url"))
        scored.append((_keyword_hit_score(text, keywords), p))
    scored.sort(key=lambda x: x[0], reverse=True)
    # keep strong matches; if none match, keep a few recent-ish items
    filtered = [p for s, p in scored if s > 0][:limit]
    return filtered if filtered else [p for _, p in scored[: min(limit, len(scored))]]


def filter_experience(experiences: List[Dict[str, Any]], keywords: Sequence[str], limit: int = 5) -> List[Dict[str, Any]]:
    scored: List[tuple[int, Dict[str, Any]]] = []
    for e in experiences:
        # Supabase schema: position, company, description, location
        text = _row_text(e, ("position", "company", "description", "location"))
        scored.append((_keyword_hit_score(text, keywords), e))
    scored.sort(key=lambda x: x[0], reverse=True)
    filtered = [e for s, e in scored if s > 0][:limit]
    return filtered if filtered else [e for _, e in scored[: min(limit, len(scored))]]


def filter_skills(skills: List[Dict[str, Any]], keywords: Sequence[str], limit: int = 30) -> List[Dict[str, Any]]:
    scored: List[tuple[int, Dict[str, Any]]] = []
    for s in skills:
        # Supabase schema: skill
        text = _row_text(s, ("skill",))
        scored.append((_keyword_hit_score(text, keywords), s))
    scored.sort(key=lambda x: x[0], reverse=True)
    filtered = [row for score, row in scored if score > 0][:limit]
    return filtered if filtered else [row for _, row in scored[: min(limit, len(scored))]]


async def enhance_with_llm(
    projects: List[Dict[str, Any]],
    job_description: str,
    keywords: Sequence[str],
    single_page_only: bool,
) -> List[Dict[str, Any]]:
    """
    Rewrite project descriptions to better align with JD (without inventing facts).
    Keeps the original fields, only updates the description field if present.
    """
    if not projects:
        return projects

    kw_str = ", ".join(_unique_preserve_order(list(keywords))[:25])
    max_projects = 4 if single_page_only else min(6, len(projects))
    to_enhance = projects[:max_projects]

    async def _rewrite_one(p: Dict[str, Any]) -> Dict[str, Any]:
        name = str(p.get("name") or p.get("title") or "Project").strip()
        desc = str(p.get("description") or p.get("summary") or "").strip()
        tech = str(p.get("tech_stack") or p.get("technologies") or p.get("tools") or "").strip()

        prompt = (
            "You are helping rewrite a resume project description to match a job description.\n"
            "Constraints:\n"
            "- Do NOT add new tools/skills not present in the original project info\n"
            "- Do NOT fabricate metrics or achievements\n"
            "- Keep it concise, impact-oriented, ATS-friendly\n"
            "- Output ONLY JSON: {\"description\": \"...\"}\n\n"
            f"JOB DESCRIPTION:\n{job_description}\n\n"
            f"TARGET KEYWORDS (for phrasing only): {kw_str}\n\n"
            f"PROJECT NAME: {name}\n"
            f"PROJECT TECH (original): {tech}\n"
            f"ORIGINAL DESCRIPTION:\n{desc}\n"
        )

        def _invoke() -> str:
            return str(model.invoke(prompt).content)

        raw = await asyncio.to_thread(_invoke)
        try:
            data = json.loads(raw)
            new_desc = str(data.get("description", "")).strip()
            if new_desc:
                out = dict(p)
                out["description"] = new_desc
                return out
        except Exception:
            pass
        return p

    enhanced = await asyncio.gather(*[_rewrite_one(p) for p in to_enhance])
    return enhanced + projects[len(to_enhance) :]


def _extract_skill_names(skills_rows: List[Dict[str, Any]]) -> List[str]:
    names: List[str] = []
    for r in skills_rows:
        v = r.get("skill")
        if isinstance(v, str) and v.strip():
            names.append(v.strip())
    return _unique_preserve_order(names)


def _matched_missing_skills(user_skills: List[str], keywords: Sequence[str]) -> Dict[str, List[str]]:
    user_norm = {_normalize_token(s): s for s in user_skills if _normalize_token(s)}
    kw_norm = {_normalize_token(k): k for k in keywords if _normalize_token(k)}

    matched = []
    missing = []

    # matched: keywords that appear in user skills
    for nkw, orig_kw in kw_norm.items():
        for ns, orig_skill in user_norm.items():
            if nkw and (nkw == ns or nkw in ns or ns in nkw):
                matched.append(orig_skill)
                break
        else:
            missing.append(orig_kw)

    return {
        "matched_skills": _unique_preserve_order(matched),
        "missing_skills": _unique_preserve_order(missing)[:25],
    }


@router.post("/generate-resume")
async def generate_resume(payload: GenerateResumeRequest):
    """
    Generate a JD-aligned resume from user's Arsenal in Supabase.
    V1 approach: keyword extraction + simple matching + LLM rewriting for projects.
    """
    try:
        arsenal = await fetch_user_arsenal(payload.user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch Supabase data: {str(e)}")

    keywords = await extract_keywords(payload.job_description)

    personal_rows = arsenal.get("personal_details", [])
    summary_rows = arsenal.get("professional_summary", [])
    objective_rows = arsenal.get("career_objectives", [])
    skills_rows = arsenal.get("skills", [])
    projects_rows = arsenal.get("projects", [])
    exp_rows = arsenal.get("professional_experience", [])
    edu_rows = arsenal.get("education", [])

    filtered_skills_rows = filter_skills(skills_rows, keywords, limit=30 if not payload.single_page_only else 18)
    filtered_projects_rows = filter_projects(projects_rows, keywords, limit=6 if not payload.single_page_only else 4)
    filtered_exp_rows = filter_experience(exp_rows, keywords, limit=6 if not payload.single_page_only else 4)

    enhanced_projects = await enhance_with_llm(
        filtered_projects_rows,
        payload.job_description,
        keywords,
        payload.single_page_only,
    )

    user_skill_names = _extract_skill_names(skills_rows)
    skill_gap = _matched_missing_skills(user_skill_names, keywords)

    # Build personal_info from personal_details + professional_summary + career_objectives
    personal_info: Optional[Dict[str, Any]] = None
    if personal_rows:
        base = dict(personal_rows[0])
        # Strip internal fields we don't need in the resume JSON
        for k in ("id", "user_id", "created_at"):
            base.pop(k, None)

        if summary_rows:
            base["professional_summary"] = summary_rows[0].get("professional_summary")
        if objective_rows:
            base["career_objective"] = objective_rows[0].get("career_objective")

        personal_info = base

    structured_resume = {
        "personal_info": personal_info,
        "skills": filtered_skills_rows,
        "projects": enhanced_projects,
        "experience": filtered_exp_rows,
        "education": edu_rows,
        "matched_skills": skill_gap["matched_skills"],
        "missing_skills": skill_gap["missing_skills"],
        "keywords": keywords,
        "meta": {
            "experience_level": payload.experience_level,
            "category": payload.category,
            "sub_category": payload.sub_category,
            "single_page_only": payload.single_page_only,
        },
    }

    supabase = get_supabase_client()

    # ---------- Upload structured resume JSON to Supabase Storage (bucket: resumes) ----------
    file_name = f"generated-resume-{int(time.time())}.json"
    file_path = f"{payload.user_id}/{file_name}"
    file_bytes = json.dumps(structured_resume, ensure_ascii=False, indent=2).encode("utf-8")

    def _upload_and_insert():
        # Upload to storage bucket "resumes"
        # Explicitly set contentType so Storage doesn't reject JSON as text/plain.
        # Upload JSON; some Supabase setups may enforce contentType.
        # If your bucket still rejects this, consider allowing "text/plain" or
        # changing this to "application/octet-stream" in your project.
        try:
            storage_res = supabase.storage.from_("resumes").upload(
                file_path,
                file_bytes,
            )
        except TypeError:
            # Fallback for clients that require explicit options but with strict typing
            storage_res = supabase.storage.from_("resumes").upload(
                file_path,
                file_bytes,
                {
                    "content-type": "application/json"
                }
            )
        # Older supabase-py returns a dict with possible "error" key; newer returns an object.
        storage_error = None
        if isinstance(storage_res, dict):
            storage_error = storage_res.get("error")
        else:
            storage_error = getattr(storage_res, "error", None)
            data_attr = getattr(storage_res, "data", None)
            if not storage_error and isinstance(data_attr, dict):
                storage_error = data_attr.get("error")
        if storage_error:
            raise RuntimeError(f"Storage upload failed: {storage_error}")

        # Insert row into resumes table
        db_res = supabase.table("resumes").insert(
            {
                "user_id": payload.user_id,
                "file_name": file_name,
                "file_path": file_path,
            }
        ).execute()

        data = getattr(db_res, "data", None)
        if not data or not isinstance(data, list):
            raise RuntimeError(f"Invalid Supabase DB response: {data}")

        row = data[0]
        if not isinstance(row, dict) or "id" not in row:
            raise RuntimeError(f"Unexpected resumes row: {row}")

        # Public URL for the stored JSON (if bucket is public)
        public = supabase.storage.from_("resumes").get_public_url(file_path)
        public_url = getattr(public, "public_url", None) or getattr(public, "data", {}).get("publicUrl")  # type: ignore[union-attr]

        return row["id"], public_url

    try:
        resume_id, public_url = await asyncio.to_thread(_upload_and_insert)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to persist resume: {str(e)}")

    return {
        "resume_id": resume_id,
        "file_name": file_name,
        "file_path": file_path,
        "file_url": public_url,
        "data": structured_resume,
    }