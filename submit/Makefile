# Makefile for LaTeX document compilation
# Main document
MAIN = main
SUPPLEMENT = supplement

# LaTeX compiler
LATEX = pdflatex
BIBTEX = bibtex
LATEX_FLAGS = -interaction=nonstopmode -halt-on-error

.PHONY: all main supplement clean cleanall view help

# Default target
all: main

# Compile main document
main: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex
	@echo "Compiling $(MAIN).tex..."
	$(LATEX) $(LATEX_FLAGS) $(MAIN).tex
	$(LATEX) $(LATEX_FLAGS) $(MAIN).tex
	@echo "✓ $(MAIN).pdf compiled successfully"

# Quick compile (single pass, for testing)
quick:
	@echo "Quick compile..."
	$(LATEX) $(LATEX_FLAGS) $(MAIN).tex

# Clean auxiliary files
clean:
	@echo "Cleaning auxiliary files..."
	rm -f *.aux *.log *.bbl *.blg *.out *.toc *.lof *.lot
	rm -f *.fdb_latexmk *.fls *.synctex.gz
	rm -f *.acn *.acr *.alg *.glg *.glo *.gls *.ist
	@echo "✓ Clean complete"

# Clean everything including PDFs
cleanall: clean
	@echo "Removing PDFs..."
	rm -f $(MAIN).pdf $(SUPPLEMENT).pdf
	@echo "✓ Clean all complete"

# View PDF (opens with default PDF viewer)
view: $(MAIN).pdf
	@if command -v xdg-open > /dev/null; then \
		xdg-open $(MAIN).pdf; \
	elif command -v open > /dev/null; then \
		open $(MAIN).pdf; \
	else \
		echo "No PDF viewer found"; \
	fi

# Show help
help:
	@echo "Available targets:"
	@echo "  make all        - Compile both main and supplement (default)"
	@echo "  make main       - Compile main.pdf"
	@echo "  make quick      - Quick compile (single pass)"
	@echo "  make clean      - Remove auxiliary files"
	@echo "  make cleanall   - Remove all generated files including PDFs"
	@echo "  make view       - Open main.pdf in default viewer"
	@echo "  make help       - Show this help message"
