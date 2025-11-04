"""LaTeX and document templates for CV generation."""

import textwrap

# LaTeX Template for CV Generation
LATEX_TEMPLATE = textwrap.dedent(r"""
    \documentclass[10pt, letterpaper]{article}

    % ========== Packages ==========
    \usepackage[
        ignoreheadfoot,
        top=2 cm,
        bottom=2 cm,
        left=2 cm,
        right=2 cm,
        headsep=1.0 cm,
        footskip=1.0 cm
    ]{geometry}
    \usepackage[explicit]{titlesec}
    \usepackage{tabularx}
    \usepackage{array}
    \usepackage[dvipsnames]{xcolor}
    \definecolor{primaryColor}{RGB}{0, 79, 144}
    \usepackage{enumitem}
    \usepackage{fontawesome5}
    \usepackage{amsmath}
    \usepackage[
        pdftitle={CV},
        pdfauthor={},
        pdfcreator={LaTeX},
        colorlinks=true,
        urlcolor=primaryColor
    ]{hyperref}
    \usepackage{paracol}
    \usepackage{changepage}
    \usepackage{ifthen}
    \usepackage{needspace}
    \usepackage{lastpage}
    \usepackage{bookmark}

    % Ensure ATS readability
    \usepackage[T1]{fontenc}
    \usepackage[utf8]{inputenc}
    \usepackage{lmodern}

    \usepackage[default]{sourcesanspro} % clean sans-serif font


    % ========== Styling ==========
    \pagestyle{empty}
    \setcounter{secnumdepth}{0}
    \setlength{\parindent}{0pt}
    \setlength{\columnsep}{0.15cm}

    \titleformat{\section}{
        \needspace{4\baselineskip}
        \Large\color{primaryColor}
    }{}{
    }{
        \textbf{#1}\hspace{0.15cm}\titlerule[0.8pt]\hspace{-0.1cm}
    }[]

    \titlespacing{\section}{-1pt}{0.3cm}{0.2cm}

    \newenvironment{highlights}{
        \begin{itemize}[
            topsep=0.10cm,
            parsep=0.10cm,
            itemsep=0pt,
            leftmargin=0.5cm
        ]
    }{
        \end{itemize}
    }

    \newenvironment{onecolentry}{
        \begin{adjustwidth}{0.2cm}{0.2cm}
    }{
        \end{adjustwidth}
    }

    \newenvironment{twocolentry}[2][]{
        \onecolentry
        \def\secondColumn{#2}
        \setcolumnwidth{\fill, 4.5cm}
        \begin{paracol}{2}
    }{
        \switchcolumn \raggedleft \secondColumn
        \end{paracol}
        \endonecolentry
    }

    % ========== Document ==========
    \begin{document}

    % ---------- Header ----------
    \begin{center}
        {\fontsize{28pt}{30pt}\selectfont \textbf{Navn}} \\[12pt]
        \small
        \faBirthdayCake \ Fødselsdato \quad | \quad
        \faEnvelope[regular] \ Epost \quad | \quad
        \faPhone* \ Telefonnummer \quad | \quad
        \faMapMarker* \ Adresse
    \end{center}

    \vspace{0.8cm}


    % ---------- Summary ----------
    \section{Sammendrag}
    \begin{onecolentry}
    Sammendrag\_tekst
    \end{onecolentry}

    % ---------- Education ----------
    \section{Utdanning}
    \begin{twocolentry}{Trinn/Ferdig\_år}
        \textbf{Grad} – Skole
        \begin{highlights}
            \item Ytterligere\_informasjon
        \end{highlights}
    \end{twocolentry}

    % ---------- Experience ----------
    \section{Arbeidserfaring}
    \subsection*{Stillinger}
    \begin{twocolentry}{Periode}
        \textbf{Tittel}, Firma
        \begin{highlights}
            \item Beskrivelse
        \end{highlights}
    \end{twocolentry}

    \vspace{0.3cm}

    \subsection*{Dugnad}
    \begin{twocolentry}{Periode}
        \textbf{Oppdrag}
        \begin{highlights}
            \item Beskrivelse
        \end{highlights}
    \end{twocolentry}

    % ---------- Skills ----------
    \section{Ferdigheter}
    \begin{onecolentry}
        \textbf{Ferdigheter og kompetanser:}
        \begin{highlights}
            \item Ferdighet (Nivå): Beskrivelse
        \end{highlights}
    \end{onecolentry}

    \begin{onecolentry}
        \textbf{Språk:} Språk (Nivå)
    \end{onecolentry}

    \begin{onecolentry}
        \textbf{Sertifikater:} \\
        Sertifikater
    \end{onecolentry}

    \begin{onecolentry}
        \textbf{Annet:} \\
        Annet
    \end{onecolentry}

    % ---------- Interests ----------
    \section{Interesser og hobbyer}
    \begin{onecolentry}
        \textbf{Interesse/Hobby} – Beskrivelse
    \end{onecolentry}

    % ---------- Future Goals ----------
    \section{Fremtidige mål}
    \begin{onecolentry}
        \textbf{Fremtidsutsikter og mål:} Fremtidsutsikter\_og\_mål
    \end{onecolentry}

    \begin{onecolentry}
        \textbf{Jobbønsker:}
        \begin{highlights}
            \item Jobbønske – Begrunnelse
        \end{highlights}
    \end{onecolentry}

    \end{document}
""")
