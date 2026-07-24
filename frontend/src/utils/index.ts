/** 格式化置信度为百分比 */
export function formatConfidence(score: number): string {
  return (score * 100).toFixed(0) + '%'
}

/** 置信度颜色 */
export function confidenceColor(score: number): string {
  if (score >= 0.9) return '#67c23a'
  if (score >= 0.7) return '#e6a23c'
  return '#f56c6c'
}

/** 学情风格中文映射 */
export function learningStyleLabel(style: string): string {
  const map: Record<string, string> = {
    theory_first: '理论先行',
    practice_first: '实操先行',
    balanced: '均衡型',
  }
  return map[style] || style
}

/** 难度标签类型 */
export function difficultyTagType(difficulty: string): string {
  const map: Record<string, string> = {
    easy: 'success',
    medium: 'warning',
    hard: 'danger',
  }
  return map[difficulty] || 'info'
}
