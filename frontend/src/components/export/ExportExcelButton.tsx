import { Button } from '@mantine/core'
import { IconFileSpreadsheet } from '@tabler/icons-react'

/** Link estilizado como botão para um endpoint de export do backend (ex.
 * GET /faturamento/export), protegido pela mesma sessão da SPA. Não usa fetch+blob:
 * uma navegação de mesma origem já envia o cookie de sessão automaticamente,
 * e o `Content-Disposition: attachment` da resposta faz o browser baixar o
 * arquivo sem sair da SPA — mais simples e não trava a aba com o workbook
 * inteiro em memória JS antes de salvar (importa em celulares mais fracos). */
export function ExportExcelButton({ href, disabled }: { href: string; disabled?: boolean }) {
  return (
    <Button
      component="a"
      href={href}
      leftSection={<IconFileSpreadsheet size={16} />}
      color="green"
      disabled={disabled}
    >
      Exportar Excel
    </Button>
  )
}
