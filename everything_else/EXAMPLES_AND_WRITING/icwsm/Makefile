TARGET=tweetmotif_icwsm10

all: quick

quick:
	pdflatex $(TARGET)
	open $(TARGET).pdf

full:
	pdflatex $(TARGET) && bibtex $(TARGET) && pdflatex $(TARGET) && pdflatex $(TARGET)
	open $(TARGET).pdf

clean:
	rm -f $(TARGET).{aux,bbl,blg,log,dvi,pdf}
