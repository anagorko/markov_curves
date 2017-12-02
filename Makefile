all: menger.pdf diamond.pdf jpg cantor_join.pdf
	# Done
jpg: diagrams/cantor_join_0.jpg diagrams/cantor_join_1.jpg diagrams/cantor_join_2.jpg diagrams/cantor_join_3.jpg diagrams/cantor_join_4.jpg diagrams/cantor_join_5.jpg diagrams/nobeling_0.jpg diagrams/nobeling_1.jpg diagrams/nobeling_2.jpg
	# JPG
diagrams/%.jpg: diagrams/%.png
	convert $< -flatten -trim -background white $@
menger.pdf: menger.tex diagrams/menger_0.jpg diagrams/menger_1.jpg diagrams/menger_2.jpg diagrams/menger_3.jpg diagrams/menger_4.jpg diagrams/menger_5.jpg
	pdflatex menger.tex
diamond.pdf: diamond.tex diagrams/diamond_0.jpg diagrams/diamond_1.jpg diagrams/diamond_2.jpg diagrams/diamond_3.jpg diagrams/diamond_4.jpg diagrams/diamond_sfdp_0.jpg \
 diagrams/diamond_sfdp_1.jpg diagrams/diamond_sfdp_2.jpg diagrams/diamond_sfdp_3.jpg diagrams/diamond_sfdp_4.jpg
	pdflatex diamond.tex
diagrams/menger_%.jpg: diagrams/menger_%.png
	convert $< -trim -fill white -opaque none $@
diagrams/diamond_%.jpg: diagrams/diamond_%.png
	convert $< -trim -fill white -opaque none $@
diagrams/diamond_sfdp_%.jpg: diagrams/diamond_sfdp_%.png
	convert $< -trim -fill white -opaque none $@
diagrams/menger_%.png: elementary.py
	./elementary.py
diagrams/diamond_%.png: elementary.py
	./elementary.py
diagrams/diamond_sfdp_%.png: elementary.py
	./elementary.py
cantor_join.pdf: cantor_join.tex jpg
	pdflatex cantor_join.tex
diagrams/nobeling_%.png: elementary.py
	./elementary.py
clean:
	rm *.aux *.log *~
