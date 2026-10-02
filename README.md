# Radio Astronomy Imaging Tool

## Summary

This GUI was developed within the scope of the EE4795: Statistical Digital Signal Processing course for the MSc EE: SNS at the TU Delft. 
The interface provides the user with an easy way of uploading matlab data files containing the estimated correlation matrix of a phased array. The data then gets processed and images are produces based on the selected  
processing algorithms. The various options are discussed below.

## Imaging Algorithms

Four imaging algorithms have been implemented which are used for imaging: Matched Beamformer, Minimum Variance Distortionless Response (MVDR), CLEAN and Adapted Angular Response (AAR).

### Matched Beamformer

The matched beamformer performs a basic scan of the region of interests and returns an estimate of the power incoming from that specific direction. This is given by the formula:

$$ P(\vec{p}) = \vec{a}^H \hat{R_x} \vec{a} $$