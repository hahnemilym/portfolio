#! /bin/csh

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# Configure environment
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

# Local Directory
setenv DIR /projects

# Project Directory
setenv MSIT_DIR $DIR/msit

# Subjects Directory
setenv SUBJECTS_DIR $MSIT_DIR/subjs

# Parameters Directory
setenv PARAMS_DIR $MSIT_DIR/bsm_params/

# Analyses Directory
setenv ANALYSIS_DIR $MSIT_DIR/msit

# Subjects List
setenv SUBJECT_LIST $PARAMS_DIR/subjects.txt

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# Define parameters
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

set study = msit
set task = (${study}_bsm)

set do_anat = 'yes'

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# Initialize subject(s) environment
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

#set subjects = ($SUBJECT_LIST)
#foreach subj ( `cat $subjects` )

set subjects = (hc009 hc018 hc019 hc021 hc028 hc031 hc036 pp004 pp006 pp007 pp012 pp015)
foreach subj ($subjects)

echo "****************************************************************"
echo " AFNI | Anatomical preprocessing "
echo "****************************************************************"

if ( ${do_anat} == 'yes' ) then

setenv DATA_DIR $SUBJECTS_DIR/${subj}/${task}

cd ${DATA_DIR}/anat

echo "****************************************************************"
echo " AFNI | 3dcopy - convert SUMA generated NIFTI to AFNI format "
echo "****************************************************************"

3dcopy ${study}.${subj}.anat.nii ${study}.${subj}.anat

echo "****************************************************************"
echo " AFNI | Configure FSL segmentation "
echo "****************************************************************"

3dresample \
-orient ASR \
-inset ${DATA_DIR}/anat/${study}.${subj}.anat+orig \
-prefix ${study}.${subj}.anat.FSL.nii

echo "****************************************************************"
echo " FSL | Segmentation: GM WM CSF "
echo "****************************************************************"

source /usr/local/freesurfer/nmr-stable60-env

fast -t 1 -n 3 -H .5 -B -b --nopve -o ${study}.${subj}.anat ${study}.${subj}.anat.FSL.nii 

echo "****************************************************************"
echo " AFNI | Revert segmented output to AFNI format "
echo "****************************************************************"

gunzip *.gz*

3dcopy \
-verb ${study}.${subj}.anat_seg.nii \
${study}.${subj}.anat.seg.float

3drefit \
-'anat' ${study}.${subj}.anat.seg.float+orig

gunzip *.gz*

echo "****************************************************************"
echo " AFNI | Convert the data type from float to short "
echo "****************************************************************"

3dcalc \
-datum short \
-a ${study}.${subj}.anat.seg.float+orig \
-expr a \
-prefix ${study}.${subj}.anat.seg.fsl

gunzip *.gz*

echo "****************************************************************"
echo " AFNI | @auto_tlrc | Copy anat to to Talairach Space "
echo "****************************************************************"

@auto_tlrc \
-no_ss \
-rmode quintic \
-base TT_N27+tlrc \
-input ${study}.${subj}.anat+orig

gunzip *.gz*

echo "****************************************************************"
echo " AFNI | @auto_tlrc | Convert FSL Segmentation to Talairach Space "
echo "****************************************************************"

@auto_tlrc \
-apar ${study}.${subj}.anat+tlrc \
-no_ss \
-rmode quintic \
-input ${study}.${subj}.anat.seg.fsl+orig

gunzip *.gz*

echo "****************************************************************"
echo "DONE"
echo "****************************************************************"

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# exit loop: anat preproc
endif

# exit loop: subjs
end

# return to project scripts
cd $ANALYSIS_DIR
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

