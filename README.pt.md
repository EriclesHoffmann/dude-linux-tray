# dude-linux-tray

Leva a **bandeirinha do MikroTik The Dude** para o Linux moderno (GNOME / Ubuntu) quando o cliente Windows roda no **Wine**.

No Windows, o The Dude mostra uma bandeira na bandeja (verde = ok, vermelho/amarelo = problema). No Wine + GNOME/Wayland isso vira uma faixa “Wine System Tray” inútil — ou some da barra.

Este projeto cola o **NotifyIcon real do Wine** na barra:

- Bandeira compacta **~16×16** (fundo branco mascarado)
- **Cor ao vivo** do The Dude
- **Minimizar → bandeira**, clique → restaurar
- **Ajustador** de posição na barra
- **Fora** da lista de apps / taskbar

> Não é produto oficial MikroTik. Não usa API do servidor — reaproveita o ícone que o cliente já desenha.

## Requisitos

- Ubuntu 22.04+ / GNOME (testado com Dash to Panel; XWayland para janelas Wine)
- Wine (prefixo win32 recomendado)
- Pacotes: `python3-xlib`, `python3-pil`, `python3-gi`, `gir1.2-gtk-3.0`, `xdotool`, `wmctrl`

## Instalação rápida

```bash
git clone https://github.com/EriclesHoffmann/dude-linux-tray.git
cd dude-linux-tray
./install.sh
```

### Wine / The Dude

1. Instale o cliente The Dude num prefixo win32 (padrão esperado: `~/.local/share/wineprefixes/dude`).
2. Preferências do Dude: ícone na bandeja **ligado**, hide on minimize **ligado**, auto-update **desligado** (recomendado).
3. Abra com `~/bin/the-dude.sh`.
4. Alinhe a bandeira: `~/bin/dude-flag-adjust.py` (setas; Shift = 8px). Posição em `~/.config/dude-flag/position.conf`.

Tela preta no Dude: o launcher já usa `LIBGL_ALWAYS_SOFTWARE=1`.

## Licença

MIT — [LICENSE](LICENSE).

Texto para o fórum MikroTik: [FORUM_POST.md](FORUM_POST.md).
