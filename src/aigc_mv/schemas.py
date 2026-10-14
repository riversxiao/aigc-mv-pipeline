"""Pydantic models for the AIGC MV pipeline."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Character(BaseModel):
    """A reusable cast member with locked identity text for prompting."""

    id: str
    display_name: str
    identity: str = Field(
        ...,
        description="Verbatim identity clause; must be pasted unchanged into prompts.",
    )
    wardrobe_default: str = ""
    style_family: str = "cinematic still, film grain, dramatic stage lighting"
    forbidden: list[str] = Field(default_factory=lambda: ["young child", "logos", "watermarks"])
    refs: list[str] = Field(default_factory=list, description="Paths or URLs to reference images.")
    notes: str = ""


class LyricSegment(BaseModel):
    text: str
    t0: float
    t1: float


class Beatmap(BaseModel):
    """Time-aligned lyrics / beats for a project audio track."""

    project: str
    duration_sec: float
    bpm: float | None = None
    segments: list[LyricSegment] = Field(default_factory=list)
    source: str = "stub"
    meta: dict[str, Any] = Field(default_factory=dict)


class Shot(BaseModel):
    """One storyboard shot pinned to the beatmap."""

    shot_id: str
    t0: float
    t1: float
    who: list[str] = Field(default_factory=list)
    framing: str = "MCU"
    action: str = ""
    plate_prompt: str = ""
    camera: str = "static"
    lyric_excerpt: str = ""


class TimelineClip(BaseModel):
    shot_id: str
    t0: float
    t1: float
    source: str = Field(..., description="Path to plate/clip file, or lavfi placeholder.")


class Timeline(BaseModel):
    project: str
    duration_sec: float
    clips: list[TimelineClip] = Field(default_factory=list)
    output: str = "edit/preview.mp4"


class ProjectBrief(BaseModel):
    """High-level creative brief for a music-video project."""

    name: str
    concept: str
    characters: list[str] = Field(default_factory=list)
    style: str = ""
    target_duration_sec: float = 30.0
    language: str = "zh"
    constraints: list[str] = Field(default_factory=list)
    budget_notes: str = ""
