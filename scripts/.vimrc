set noet 
set smarttab 
set expandtab        " Tab key inserts spaces instead of tabs
set tabstop=4        " Sets the tab size to 4
set shiftwidth=4     " Sets spaces used for (auto)indent
set shiftround       " Indent to nearest tabstop
set autoindent       " Carries over previous indent to the next line
set softtabstop=4
filetype indent on
set autoindent
set wrap
set ignorecase
set ruler
set showcmd
set noswapfile
"set showbreak=\
set laststatus=2
set showmatch
set wildmenu
set complete-=k complete+=k/usr/share/dict/*
set history=80
"set statusline=[%n]\ %<%f\ %((%M%*%R%Y)%)\ %=%-19(\LINE\ [%3l/%3L]\ COL\ [%02c%03V]%)\ %P
set makeef=~/vim.err
"set makeprg=makewrap.sh
set wim=longest:full
set winminheight=0
"disable F1"
map <F1> <esc>
imap <F1> <esc>
set background=dark
"set list     # set $ on new line
