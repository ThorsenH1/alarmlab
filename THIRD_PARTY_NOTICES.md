# Third-party data and software

## UCI 447 derived data

The file data/external/uci447_features.csv.gz is derived from:

Helwig, N., Pignanelli, E., and Schütze, A. (2015). **Condition monitoring of hydraulic systems**. UCI Machine Learning Repository. [https://doi.org/10.24432/C5CW21](https://doi.org/10.24432/C5CW21).

The source dataset is licensed under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/). The derived table remains under that licence. No endorsement by the dataset creators is implied.

Changes: selected nine physical sensor channels; computed mean, population standard deviation, range and normalized-time slope for each cycle; retained cycle numbers and condition annotations. The original matrices are not redistributed in this repository.

Source and derived-file fingerprints are recorded in data/external/uci447_provenance.json.

## Software dependencies

NumPy, pandas, SciPy, scikit-learn and Matplotlib retain their respective licences. Playwright is a development-only browser-verification dependency. Their source or binaries are not copied into the repository.

The project uses installed fonts supplied by the operating system; it does not redistribute font files. All interface illustrations and scientific plots are drawn by project code.

## References

Public IFE descriptions and the job advert are linked for context. Their full text, logos and other assets are not redistributed.
