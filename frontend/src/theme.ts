import { createTheme, type MantineColorsTuple } from '@mantine/core'

// Rampa de azul derivada da paleta já usada nos clients desktop (Tkinter):
// primária #1a5276, accent #2980b9. Índice 6 (accent) é o tom padrão usado
// por botões/links no tema claro; índice 8 (primária escura) no tema escuro.
const primary: MantineColorsTuple = [
  '#eaf3fb',
  '#d3e6f6',
  '#a7cdec',
  '#79b3e1',
  '#529cd8',
  '#3a8cd1',
  '#2980b9',
  '#22699c',
  '#1a5276',
  '#123a54',
]

export const theme = createTheme({
  primaryColor: 'primary',
  colors: { primary },
  defaultRadius: 'md',
  fontFamily: '"Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif',
})
