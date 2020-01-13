#!/usr/bin/env python3

"""
__author__ = "Axelle Apvrille"
__license__ = "MIT License"
"""
import argparse
import os
import subprocess
import droidutil # that's my own utilities
import droidsample
import droiddesc

property_dump_file = 'autoanalysis.md'
description_file = 'description.md'
__version__ = "3.0"

def get_arguments():
    """Read arguments for the program and returns the ArgumentParser"""

    parser = argparse.ArgumentParser(description='''DroidLysis3 is a Python 
script which processes Android samples. 

1/ It extracts properties from the samples (e.g connects to Internet, roots the phone...). The extracted properties are displayed.
2/ It helps the analyst begin its reverse engineering of the sample, by performing a first automatic analysis, disassembling, decompiling and a description draft.''', prog='DroidLysis', epilog='Version '+__version__+' - Greetz from Axelle Apvrille')
    parser.add_argument('-i', '--input', help='input directories or files to process', nargs='+', action='store', default='.')
    parser.add_argument('-o', '--output', help='analysis of input files is written into subdirectories of this directory', action='store', default='.')
    parser.add_argument('-c', '--clearoutput', help='erase the output directory at the end. Indicates you want something quick.', action='store_true')
    parser.add_argument('-m', '--movein', help='after it has been processed, each input file is moved to this directory', action='store')
    parser.add_argument('-v', '--verbose', help='get more detailed messages', action='store_true')
    parser.add_argument('-V', '--version', help='displays version number', action='version', version="%(prog)s "+__version__)
    parser.add_argument('--no-kit-exception', help='by default, ad/dev/stats kits are ruled out for searches. Use this option to treat them as regular namespaces', action='store_true')
    parser.add_argument('--enable-procyon', help='enable procyon decompilation', action='store_true')
    parser.add_argument('--disable-description', help='do not generate automatic description', action='store_true')
    parser.add_argument('--disable-sql', help='do not write analysis to SQL database', action='store_true')

    args = parser.parse_args()
    
    # create output dir if necessary
    droidutil.mkdir_if_necessary(args.output)
    
    # create movein dir if necessary
    if args.verbose and args.movein:
        print("Creating %s if necessary" % (args.movein))
    droidutil.mkdir_if_necessary(args.movein)

    return args

def process_input(args):
    """
    Process input. 
    Provide ArgumentParser as argument.
    
    args.input contains a list of files and directories to process.
    each file in an input directory are processed, but not recursively.
    each input file is process.

    """
    for element in args.input:
        if os.path.isdir(element): 
            listing = os.listdir(element)
            for file in listing:
                process_file(os.path.join(element, file), args.output, args.verbose, args.clearoutput, args.enable_procyon, args.disable_description, args.no_kit_exception, args.disable_sql)
                if args.movein:
                    if args.verbose:
                        print("Moving %s to %s" % (os.path.join('.',element), os.path.join(args.movein, element)))
                    # TODO: issue if inner dirs. Are we handling this?
                    try: 
                        os.rename(os.path.join(element, file), os.path.join(args.movein, file))
                    except OSError as e:
                        if args.verbose:
                            print( "%s no longer present?: %s\n" % (file, str(e)))

        if os.path.isfile(element):
            process_file(os.path.join('.',element), args.output, args.verbose, args.clearoutput, args.enable_procyon, args.disable_description, args.no_kit_exception)
            # dirname = os.path.join(args.output, '{filename}-*'.format(filename=element))
            if args.movein:
                if args.verbose:
                    print("Moving %s to %s" % (os.path.join('.',element), os.path.join(args.movein, os.path.basename(element))))
                os.rename(os.path.join('.',element), os.path.join(args.movein, os.path.basename(element)))


def process_file(infile, outdir='/tmp/analysis', verbose=False, clear=False, enable_procyon=False, disable_description=False, no_kit_exception=False, disable_sql=False):
    """Static analysis of a given file"""

    if os.access(infile, os.R_OK): 
        print("Processing: " + infile + " ...")
        sample = droidsample.droidsample(infile, outdir, verbose, clear, enable_procyon, disable_description, no_kit_exception)
        sample.unzip()
        sample.disassemble()
        sample.extract_file_properties()
        sample.extract_meta_properties()
        sample.extract_manifest_properties()
        sample.extract_dex_properties()
        listofkits = sample.extract_kit_properties()
        if no_kit_exception:
            listofkits = []
        sample.extract_smali_properties(listofkits)
        sample.extract_wide_properties(listofkits)

        if not disable_sql:
            sample.properties.write()

        if not clear:
            if not disable_description:
                description = droiddesc.droiddesc(sample)
                description.write_description(os.path.join(sample.outdir, description_file), verbose)
            
            analysis_file = open(os.path.join(sample.outdir, property_dump_file), 'a')
            analysis_file.write(str(sample.properties))
            analysis_file.close()
        else:
            print("Removing directory %s ..." % (sample.outdir))
            proc = subprocess.Popen(['rm', '-rf', sample.outdir])
            proc.communicate()

        sample.close()
    

if __name__ == "__main__":
    args = get_arguments()
    process_input(args)
    print("END")


