echo "

## Интерактивный режим

Для интерактивной работы используйте:

\`\`\`bash
python main.py
# или
python main.py --interactive
\`\`\`

В интерактивном режиме доступны те же команды, но без префиксов \`--\`:

\`\`\`
valutatrade> register --username alice --password 1234
valutatrade> login --username alice --password 1234  
valutatrade(alice)> buy --currency BTC --amount 0.1
valutatrade(alice)> show_portfolio
valutatrade(alice)> exit
\`\`\`

## Одиночные команды

Для выполнения одиночных команд:

\`\`\`bash
python main.py register --username alice --password 1234
python main.py login --username alice --password 1234
python main.py show-portfolio
\`\`\`
" >> README.md