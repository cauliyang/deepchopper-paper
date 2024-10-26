.PHONY: submit zip clean

# Define source and destination directories
SRC_DIR = journal_nbt
SUBMIT_DIR = submit
FIGURES_DIR = submit/figures

# List of files to copy
TEX_FILES = sn-article.tex sn-jnl.cls sn-basic.bst
FIGURE_FILES = figure1.pdf figure2.pdf sf1.pdf sf2.pdf sf3.pdf

# Create submit directory and copy files
submit: clean
	mkdir -p $(SUBMIT_DIR)
	mkdir -p $(FIGURES_DIR)
	$(foreach file,$(TEX_FILES),cp $(SRC_DIR)/$(file) $(SUBMIT_DIR)/;)
	$(foreach file,$(FIGURE_FILES),cp figures/finals/$(file) $(FIGURES_DIR)/;)

# Create zip archive
zip: submit
	zip -r submit.zip $(SUBMIT_DIR)

# Clean up
clean:
	rm -rf $(SUBMIT_DIR) submit.zip
