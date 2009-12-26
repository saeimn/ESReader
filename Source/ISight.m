/**
 * Copyright (c) 2009 Simon Hofer
 * 
 * Permission is hereby granted, free of charge, to any person
 * obtaining a copy of this software and associated documentation
 * files (the "Software"), to deal in the Software without
 * restriction, including without limitation the rights to use,
 * copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following
 * conditions:
 * 
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
 * OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 * HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 * WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
 * OTHER DEALINGS IN THE SOFTWARE.
 */

#import "ISight.h"


@implementation ISight

- (QTCaptureSession *)start
{
    hasFrame = NO;
    frame = nil;
    session = [[QTCaptureSession alloc] init];
    isight = [QTCaptureDevice defaultInputDeviceWithMediaType:QTMediaTypeVideo];
    [isight open:nil];
    
    input = [QTCaptureDeviceInput deviceInputWithDevice:isight];
    [session addInput:input error:nil];
    
    output = [[QTCaptureDecompressedVideoOutput alloc] init];
    [output setDelegate:self];
    NSDictionary *attr = [NSDictionary dictionaryWithObjectsAndKeys:
                          [NSNumber numberWithDouble:640.0], kCVPixelBufferWidthKey,
                          [NSNumber numberWithDouble:480.0], kCVPixelBufferHeightKey,
                          [NSNumber numberWithUnsignedInt:kCVPixelFormatType_32ARGB], kCVPixelBufferPixelFormatTypeKey, nil];
    [output setPixelBufferAttributes:attr];
    [session addOutput:output error:nil];
    
    [session startRunning];
    
    return session;
}

- (void)stop
{
    [session stopRunning];
    [session release];
    session = nil;
    [input release];
    input = nil;
    [output release];
    output = nil;
    if (hasFrame) {
        CVBufferRelease(frame);
    }
}

- (NSImage *)consumeFrame
{
    if (hasFrame) {
        CVImageBufferRef cvFrame = frame;
        CIImage *coreImage = [CIImage imageWithCVImageBuffer:cvFrame];
        CVBufferRelease(cvFrame);
        NSImageRep *imageRep = [[[NSBitmapImageRep alloc] initWithCIImage:coreImage] autorelease];
        NSImage *image = [[NSImage alloc] initWithSize:[imageRep size]];
        [image addRepresentation:imageRep];
        
        hasFrame = NO;
        
        return [image autorelease];
    } else {
        return nil;
    }
}


- (void)captureOutput:(QTCaptureOutput *)captureOutput
  didOutputVideoFrame:(CVImageBufferRef)videoFrame
     withSampleBuffer:(QTSampleBuffer *)sampleBuffer
       fromConnection:(QTCaptureConnection *)connection
{
    if (!hasFrame) {
        frame = CVBufferRetain(videoFrame);
        hasFrame = YES;
    }
}

@end
