"""Skills loader for markdown-based skill definitions."""
from pathlib import Path
from typing import Dict, Any, List, Optional
import re


def load_skills(skill_name: str, skills_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load a skill definition from markdown file.
    
    Args:
        skill_name: Name of skill (filename without .md)
        skills_dir: Optional custom skills directory
        
    Returns:
        Skill definition dict with name, prompt, metadata
    """
    if skills_dir is None:
        skills_dir = Path(__file__).parent / "skills"
    
    skill_file = skills_dir / f"{skill_name}.md"
    
    if not skill_file.exists():
        raise ValueError(f"Skill {skill_name} not found at {skill_file}")
    
    with open(skill_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Parse frontmatter if present
    metadata = {}
    prompt = content
    
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = parts[1]
            prompt = parts[2].strip()
            
            # Simple YAML-like parsing
            for line in frontmatter.strip().split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    metadata[key.strip()] = value.strip().strip('"\'')
    
    return {
        "name": skill_name,
        "prompt": prompt,
        "metadata": metadata,
    }


def load_all_skills(skills_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load all skill definitions from skills directory.
    
    Args:
        skills_dir: Optional custom skills directory
        
    Returns:
        List of skill definition dicts
    """
    if skills_dir is None:
        skills_dir = Path(__file__).parent / "skills"
    
    if not skills_dir.exists():
        return []
    
    skills = []
    
    for skill_file in skills_dir.glob("*.md"):
        skill_name = skill_file.stem
        try:
            skill = load_skills(skill_name, skills_dir)
            skills.append(skill)
        except Exception as e:
            print(f"Warning: Failed to load skill {skill_name}: {e}")
    
    return skills
