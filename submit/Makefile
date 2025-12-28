# Makefile for Nature Communications with glossaries support

MAIN = main
SUPP = supplement

# Compilers
LATEX = pdflatex
BIBTEX = bibtex
MAKEGLOSSARIES = makeglossaries

# Flags
LATEX_FLAGS = -interaction=nonstopmode -halt-on-error

# Auxiliary extensions to clean
AUX_EXT = aux log bbl blg out toc lof lot fls fdb_latexmk synctex.gz \
          nav snm vrb bcf run.xml xwm dvi ps

# Glossary extensions
GLOS_EXT = glo gls glg ist acn acr alg

# Backup files
BACKUP = *~ *.backup

.PHONY: clean cleanall help

# Clean auxiliary and glossary files, keep PDFs
clean:
	@echo "Cleaning auxiliary files..."
	@for ext in $(AUX_EXT) $(GLOS_EXT); do \
		rm -f $(MAIN).$$ext $(SUPP).$$ext; \
	done
	@rm -f $(BACKUP)
	@echo "✓ Auxiliary files cleaned. PDFs preserved."

# Clean everything including PDFs
cleanall: clean
	@echo "Removing PDFs..."
	@rm -f $(MAIN).pdf $(SUPP).pdf
	@echo "✓ All generated files removed."

# Help
help:
	@echo "Available targets:"
	@echo "  all        - Compile both main and supplement (default)"
	@echo "  clean      - Remove auxiliary files, keep PDFs"
	@echo "  cleanall   - Remove all generated files including PDFs"
	@echo "  help       - Show this help message"
