from dataclasses import dataclass
from typing import Optional


@dataclass
class PhotoRequirement:
    name: str
    width_px: int
    height_px: int
    min_size_kb: Optional[float]
    max_size_kb: Optional[float]
    format: str = "JPG"
    notes: str = ""


@dataclass
class ExamPreset:
    exam_name: str
    full_name: str
    photo: PhotoRequirement
    signature: Optional[PhotoRequirement] = None


EXAM_PRESETS: dict[str, ExamPreset] = {
    "ssc": ExamPreset(
        exam_name="SSC",
        full_name="Staff Selection Commission",
        photo=PhotoRequirement(
            name="SSC Photo",
            width_px=100,
            height_px=120,
            min_size_kb=20,
            max_size_kb=50,
            notes="Passport size, white background",
        ),
        signature=PhotoRequirement(
            name="SSC Signature",
            width_px=140,
            height_px=60,
            min_size_kb=10,
            max_size_kb=20,
            notes="Sign on plain white paper",
        ),
    ),
    "upsc": ExamPreset(
        exam_name="UPSC",
        full_name="Union Public Service Commission",
        photo=PhotoRequirement(
            name="UPSC Photo",
            width_px=300,
            height_px=300,
            min_size_kb=40,
            max_size_kb=300,
            notes="Recent passport size photo",
        ),
        signature=PhotoRequirement(
            name="UPSC Signature",
            width_px=300,
            height_px=100,
            min_size_kb=None,
            max_size_kb=300,
        ),
    ),
    "railway": ExamPreset(
        exam_name="Railway",
        full_name="Railway Recruitment Board (RRB)",
        photo=PhotoRequirement(
            name="RRB Photo",
            width_px=150,
            height_px=200,
            min_size_kb=20,
            max_size_kb=50,
        ),
        signature=PhotoRequirement(
            name="RRB Signature",
            width_px=150,
            height_px=70,
            min_size_kb=10,
            max_size_kb=30,
        ),
    ),
    "banking": ExamPreset(
        exam_name="Banking",
        full_name="IBPS / SBI Banking Exams",
        photo=PhotoRequirement(
            name="Banking Photo",
            width_px=200,
            height_px=230,
            min_size_kb=20,
            max_size_kb=50,
        ),
        signature=PhotoRequirement(
            name="Banking Signature",
            width_px=200,
            height_px=80,
            min_size_kb=10,
            max_size_kb=20,
        ),
    ),
    "state_psc": ExamPreset(
        exam_name="State PSC",
        full_name="State Public Service Commission",
        photo=PhotoRequirement(
            name="State PSC Photo",
            width_px=150,
            height_px=200,
            min_size_kb=10,
            max_size_kb=100,
            notes="Requirements may vary by state",
        ),
        signature=PhotoRequirement(
            name="State PSC Signature",
            width_px=150,
            height_px=80,
            min_size_kb=None,
            max_size_kb=50,
        ),
    ),
    "police": ExamPreset(
        exam_name="Police",
        full_name="Police Recruitment Board",
        photo=PhotoRequirement(
            name="Police Recruitment Photo",
            width_px=200,
            height_px=230,
            min_size_kb=20,
            max_size_kb=100,
        ),
        signature=PhotoRequirement(
            name="Police Signature",
            width_px=200,
            height_px=80,
            min_size_kb=None,
            max_size_kb=50,
        ),
    ),
    "army": ExamPreset(
        exam_name="Army",
        full_name="Indian Army Recruitment",
        photo=PhotoRequirement(
            name="Army Photo",
            width_px=350,
            height_px=350,
            min_size_kb=20,
            max_size_kb=200,
        ),
        signature=PhotoRequirement(
            name="Army Signature",
            width_px=280,
            height_px=90,
            min_size_kb=None,
            max_size_kb=100,
        ),
    ),
    "teaching": ExamPreset(
        exam_name="Teaching",
        full_name="CTET / State TET / NVS / KVS",
        photo=PhotoRequirement(
            name="Teaching Exam Photo",
            width_px=100,
            height_px=120,
            min_size_kb=10,
            max_size_kb=100,
        ),
        signature=PhotoRequirement(
            name="Teaching Exam Signature",
            width_px=140,
            height_px=60,
            min_size_kb=None,
            max_size_kb=30,
        ),
    ),
}
