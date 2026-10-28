# Kontrollen av skalet i Terminal, före och efter installationen av vakten (INSTALLERA.md, steg 4 g och
# kontrollen efter installationen, steg 1). Hugos beslut 2026-10-28 efter granskning 15: kontrollerna i steg 4
# (alias, funktioner, kroklistor, fpath och startfiler) ligger i ett skript som bara läser. Hugo eller Casper
# kontrollerar skriptets kontrollsumma och kör det i ett nytt Terminal-fönster med
#
#     source ~/VERA/agent/sparr/kontrollera-skalet.zsh
#
# Skriptet ändrar ingenting: allt körs i en funktion utan namn, med lokala variabler och inställningar, så
# att inget finns kvar i skalet efteråt. Det skriver OK, eller en rad som börjar med AVVIKER för varje sak som
# inte är väntad, och sist SLUT. Saknas SLUT har något dolt utskriften: stoppa och fråga.
#
# Det väntade, med besluten:
# - alias: exakt run-help=man och which-command=whence, inga globala alias och inga alias för filändelser
#   (granskning 13, P1 a, och granskning 14, R3).
# - funktioner: bara de väntade namnen (granskning 14, R3, och Hugos svar 2026-10-28 efter granskning 14,
#   punkt 1). Varje annan funktion avviker, också de som zsh kör av sig själv (TRAP..., preexec och liknande).
#   add-zsh-hook, som Terminals fil läser in, godtas bara från zsh:s egen mapp
#   /usr/share/zsh/<version>/functions, och filen ska ägas av root utan skrivrätt för gruppen eller andra
#   (Hugos beslut 2026-10-28 efter granskning 16, G4).
# - kroklistor: i Terminal exakt update_terminal_cwd i precmd_functions och shell_session_update i
#   zshexit_functions, de andra tomma. Båda funktionerna ska komma från /etc/zshrc_Apple_Terminal (whence -v),
#   och /etc/zshrc och /etc/zshrc_Apple_Terminal ska ägas av root utan skrivrätt för gruppen eller andra
#   (ls -l) (Hugos beslut 2026-10-28 efter granskning 15, 8 d).
# - fpath: bara zsh:s egna mappar, som ägs av root utan skrivrätt för gruppen eller andra (granskning 14, R1).
# - startfiler: bara nvm:s två rader läser in andra filer, ingen kompilerad startfil (.zwc) och ingen ZDOTDIR
#   (granskning 14, R2, och granskning 15, S2).
# - ägare och rättigheter (ls -le@): inga extra rättigheter (+), och ingen extra uppgift (@) utom exakt en, som
#   heter exakt com.apple.provenance (Hugos beslut 2026-10-28 efter granskning 17, H1).

() {
  emulate -L zsh
  setopt extended_glob

  local terminalfil=/etc/zshrc_Apple_Terminal
  local -a etcfiler=(/etc/zshrc /etc/zshrc_Apple_Terminal)
  local -a agare=(root)
  local -a avvikelser match mbegin mend
  local namn varde fil rad text mapp

  # Ägs av någon i agare, ingen skrivrätt för gruppen eller andra, inga extra rättigheter (+), och ingen länk.
  # Den enda extra uppgiften (@) som godtas är exakt com.apple.provenance, som macOS själv sätter, och då bara om
  # den är ensam (Hugos beslut 2026-10-28 efter granskning 17, H1). ls -le@ skriver varje uppgift och varje extra
  # rättighet på en egen rad efter den första, och ls visar bara @ när filen har både uppgifter och extra
  # rättigheter. Skriver felet, eller ingenting om allt är rätt.
  _vera_kontrollera_agare() {
    local sokvag=$1 rad tecken
    local -a rader ord
    rad=$(/bin/ls -lde@ -- $sokvag 2>/dev/null)
    if [[ -z $rad ]]; then
      builtin print -r -- "$sokvag finns inte"
      return
    fi
    rader=("${(@f)rad}")
    ord=(${=rader[1]})
    tecken=${ord[1]}
    if [[ $tecken == ?(#c10)@ && ${#rader} == 2 &&
          ${rader[2]} == $'\t'com.apple.provenance$'\t'[[:space:]]#[0-9]##[[:space:]]# ]]; then
      tecken=${tecken[1,10]}
    elif (( ${#rader} != 1 )); then
      tecken+=-
    fi
    if [[ $tecken == l* ]]; then
      builtin print -r -- "$sokvag är en länk: ${(j: | :)rader}"
    elif (( ${#tecken} != 10 )); then
      builtin print -r -- "$sokvag har extra rättigheter eller uppgifter (+ eller @): ${(j: | :)rader}"
    elif [[ ${ord[1][6]} == w || ${ord[1][9]} == w ]]; then
      builtin print -r -- "gruppen eller andra kan skriva i $sokvag: $rad"
    elif (( ! ${agare[(Ie)${ord[3]}]} )); then
      builtin print -r -- "$sokvag ägs inte av root: $rad"
    fi
  }

  # Alias.
  for namn varde in ${(kv)aliases}; do
    if [[ $namn=$varde != (run-help=man|which-command=whence) ]]; then
      avvikelser+=("alias: $namn=$varde")
    fi
  done
  for namn in run-help which-command; do
    (( ${+aliases[$namn]} )) || avvikelser+=("alias saknas: $namn")
  done
  for namn varde in ${(kv)galiases}; do
    avvikelser+=("globalt alias: $namn=$varde")
  done
  for namn varde in ${(kv)saliases}; do
    avvikelser+=("alias för filändelse: $namn=$varde")
  done

  # Funktioner. Väntade: zsh:s hjälp för tabb (_...), nvm, Terminals egna och de nio från compinit och
  # bashcompinit. Namnen kommer som argument från skalet utanför den här funktionen (sist i filen): inne i en
  # funktion visar zsh inte TRAPEXIT.
  for namn in ${@:#(_*|nvm*|shell_session*|update_terminal_cwd|compinit|compdef|compdump|compaudit|compinstall|bashcompinit|compgen|complete|getent|add-zsh-hook)}; do
    avvikelser+=("funktion: $namn")
  done
  # add-zsh-hook (G4): bara från zsh:s egen mapp, och filen ska ägas av root.
  if (( ${@[(Ie)add-zsh-hook]} )); then
    rad=$(whence -v -- add-zsh-hook)
    if [[ $rad == (#b)"add-zsh-hook is a shell function from "(/usr/share/zsh/[^/]##/functions/add-zsh-hook) ]]; then
      rad=$(_vera_kontrollera_agare ${match[1]})
      [[ -z $rad ]] || avvikelser+=("ls -l: $rad")
    else
      avvikelser+=("whence -v: $rad")
    fi
  fi

  # Kroklistor (8 d).
  [[ ${(j: :)preexec_functions} == '' ]] || avvikelser+=("preexec_functions=(${(j: :)preexec_functions})")
  [[ ${(j: :)precmd_functions} == update_terminal_cwd ]] || avvikelser+=("precmd_functions=(${(j: :)precmd_functions})")
  [[ ${(j: :)chpwd_functions} == '' ]] || avvikelser+=("chpwd_functions=(${(j: :)chpwd_functions})")
  [[ ${(j: :)periodic_functions} == '' ]] || avvikelser+=("periodic_functions=(${(j: :)periodic_functions})")
  [[ ${(j: :)zshaddhistory_functions} == '' ]] || avvikelser+=("zshaddhistory_functions=(${(j: :)zshaddhistory_functions})")
  [[ ${(j: :)zshexit_functions} == shell_session_update ]] || avvikelser+=("zshexit_functions=(${(j: :)zshexit_functions})")
  for namn in update_terminal_cwd shell_session_update; do
    rad=$(whence -v -- $namn)
    [[ $rad == "$namn is a shell function from $terminalfil" ]] || avvikelser+=("whence -v: $rad")
  done
  for fil in $etcfiler; do
    rad=$(_vera_kontrollera_agare $fil)
    [[ -z $rad ]] || avvikelser+=("ls -l: $rad")
  done

  # fpath (R1).
  for mapp in $fpath; do
    [[ $mapp == (/usr/share/zsh/*|/usr/local/share/zsh/site-functions) ]] || avvikelser+=("fpath: $mapp")
  done
  for mapp in $fpath /usr/local /usr/local/share /usr/local/share/zsh /usr/local/share/zsh/site-functions; do
    [[ -e $mapp ]] || continue
    rad=$(_vera_kontrollera_agare $mapp)
    [[ -z $rad ]] || avvikelser+=("ls -ld: $rad")
  done

  # Startfiler (R2 och S2).
  [[ -z $ZDOTDIR ]] || avvikelser+=("ZDOTDIR=$ZDOTDIR")
  for fil in ~/.zshenv ~/.zprofile ~/.zshrc ~/.zlogin ~/.zlogout; do
    [[ ! -e $fil.zwc ]] || avvikelser+=("kompilerad startfil: $fil.zwc")
  done
  for fil in ~/.zshenv ~/.zprofile ~/.zshrc ~/.zlogin; do
    [[ -e $fil ]] || continue
    for rad in "${(@f)$(/usr/bin/grep -n -E 'source|\. |eval|compinit|autoload|fpath|ZDOTDIR' -- $fil)}"; do
      [[ -n $rad ]] || continue
      text=${${rad#*:}%%\#*}
      text=${text%%[[:space:]]#}
      if [[ $fil != ~/.zshrc || ( $text != '[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"' &&
            $text != '[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"' ) ]]; then
        avvikelser+=("startfil: $fil:$rad")
      fi
    done
  done

  unfunction _vera_kontrollera_agare
  if (( ${#avvikelser} )); then
    builtin print -rl -- "AVVIKER: "${^avvikelser}
  else
    builtin print -r -- OK
  fi
  builtin print -r -- SLUT
} "${(@ko)functions[@]}"
