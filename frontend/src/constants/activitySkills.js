import {
  GraduationCap,
  Globe2,
  HandHeart,
  HeartPulse,
  Leaf,
  Lightbulb,
  Palette,
  Rocket,
  Scale,
  Sparkles,
  Trees
} from 'lucide-vue-next'

// key ต้องตรงกับ STAFF_SKILL_DEFINITIONS / PARTICIPANT_SKILL_DEFINITIONS ใน backend/main.py
export const STAFF_SKILLS = [
  {
    key: 'creative_leadership',
    label: 'Creative Leadership',
    description: 'ภาวะผู้นำเชิงสร้างสรรค์',
    icon: Lightbulb
  },
  {
    key: 'innovation',
    label: 'Innovation',
    description: 'การคิดและสร้างนวัตกรรม',
    icon: Sparkles
  },
  {
    key: 'entrepreneurship',
    label: 'Entrepreneurship',
    description: 'ความเป็นผู้ประกอบการ',
    icon: Rocket
  },
  {
    key: 'promote_equality',
    label: 'Promote Equality',
    description: 'การส่งเสริมความเท่าเทียม',
    icon: Scale
  },
  {
    key: 'academic',
    label: 'Academic',
    description: 'ทักษะทางวิชาการ',
    icon: GraduationCap
  },
  {
    key: 'nature_environmental',
    label: 'Nature and Environmental',
    description: 'ธรรมชาติและสิ่งแวดล้อม',
    icon: Leaf
  }
]

export const PARTICIPANT_SKILLS = [
  {
    key: 'arts_culture_traditions',
    label: 'Arts, Culture, and Traditions',
    description: 'ศิลปะ วัฒนธรรม และประเพณี',
    icon: Palette
  },
  {
    key: 'volunteerism',
    label: 'Volunteerism',
    description: 'จิตอาสาและการมีส่วนร่วมเพื่อสังคม',
    icon: HandHeart
  },
  {
    key: 'academics',
    label: 'Academics',
    description: 'การเรียนรู้และพัฒนาทางวิชาการ',
    icon: GraduationCap
  },
  {
    key: 'internationalization',
    label: 'Internationalization',
    description: 'ความเป็นสากลและการเรียนรู้ข้ามวัฒนธรรม',
    icon: Globe2
  },
  {
    key: 'health_promotion',
    label: 'Health Promotion',
    description: 'การส่งเสริมสุขภาพและความเป็นอยู่ที่ดี',
    icon: HeartPulse
  },
  {
    key: 'nature_environmental_conservation',
    label: 'Nature and Environmental Conservation',
    description: 'การอนุรักษ์ธรรมชาติและสิ่งแวดล้อม',
    icon: Trees
  }
]

export const SKILLS_BY_ROLE = {
  staff: STAFF_SKILLS,
  participant: PARTICIPANT_SKILLS
}

// สร้างชุด level เริ่มต้นให้ทุก skill ของ role นั้น
export function defaultSkillLevels(definitions, level = 3) {
  return Object.fromEntries(
    definitions.map((skill) => [skill.key, level])
  )
}

// รวม skill ที่บันทึกไว้เข้ากับทุก definition (ใช้ตอนเปิดแก้ไข)
// skill ที่ไม่มีใน saved = ไม่เกี่ยวข้อง (null) ไม่ใช่ level 3
export function skillLevelsFromSaved(definitions, saved = {}) {
  return Object.fromEntries(
    definitions.map((skill) => [skill.key, saved?.[skill.key] ?? null])
  )
}
