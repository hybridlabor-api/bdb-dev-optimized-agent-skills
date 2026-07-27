import { commonSchemas } from '../../../catalog/tool-definition-utils.js';

export const manageBlueprintWidgetProperties = {
path: commonSchemas.directoryPathForCreation,
folder: commonSchemas.directoryPath,
widgetPath: commonSchemas.widgetPath,
slotName: commonSchemas.slotName,
parentSlot: { type: 'string', description: 'Parent slot to add widget to.' },
anchorMin: {
                  type: 'object',
                  properties: commonSchemas.vector2.properties,
                  description: 'Minimum anchor point (0-1).'
                },
anchorMax: {
                  type: 'object',
                  properties: commonSchemas.vector2.properties,
                  description: 'Maximum anchor point (0-1).'
                },
alignment: {
                  type: 'object',
                  properties: commonSchemas.vector2.properties,
                  description: 'Widget alignment (0-1).'
                },
zOrder: { type: 'number', description: 'Z-order for canvas slot.' },
translation: {
                  type: 'object',
                  properties: commonSchemas.vector2.properties,
                  description: 'Render translation.'
                },
shear: {
                  type: 'object',
                  properties: commonSchemas.vector2.properties,
                  description: 'Render shear.'
                },
angle: commonSchemas.angle,
visibility: {
                  type: 'string',
                  enum: ['Visible', 'Collapsed', 'Hidden', 'HitTestInvisible', 'SelfHitTestInvisible'],
                  description: 'Widget visibility state.'
                },
clipping: {
                  type: 'string',
                  enum: ['Inherit', 'ClipToBounds', 'ClipToBoundsWithoutIntersecting', 'ClipToBoundsAlways', 'OnDemand'],
                  description: 'Widget clipping mode.'
                },
text: commonSchemas.text,
fontSize: { type: 'number', description: 'Font size.' },
colorAndOpacity: {
                  type: 'object',
                  properties: commonSchemas.colorObject.properties,
                  description: 'Color and opacity (0-1 values).'
                },
autoWrap: { type: 'boolean', description: 'Enable text auto-wrap.' },
texturePath: commonSchemas.texturePath,
brushSize: {
                  type: 'object',
                  properties: commonSchemas.vector2.properties,
                  description: 'Brush/image size.'
                },
isEnabled: { type: 'boolean', description: 'Widget enabled state.' },
isChecked: { type: 'boolean', description: 'Checkbox checked state.' },
minValue: commonSchemas.minValue,
maxValue: commonSchemas.maxValue,
stepSize: { type: 'number', description: 'Value step size.' },
delta: { type: 'number', description: 'Spinbox increment.' },
percent: { type: 'number', description: 'Progress bar percentage (0-1).' },
fillColorAndOpacity: {
                  type: 'object',
                  properties: commonSchemas.colorObject.properties,
                  description: 'Fill color for progress bar.'
                },
isMarquee: { type: 'boolean', description: 'Progress bar marquee mode.' },
inputType: { type: 'string', enum: ['single', 'multi'], description: 'Text input type.' },
hintText: { type: 'string', description: 'Placeholder hint text.' },
options: {
                  type: 'array',
                  items: commonSchemas.stringProp,
                  description: 'Combo box options.'
                },
selectedOption: { type: 'string', description: 'Selected combo box option.' },
orientation: {
                  type: 'string',
                  enum: ['Horizontal', 'Vertical'],
                  description: 'Widget orientation.'
                },
scrollBarVisibility: {
                  type: 'string',
                  enum: ['Visible', 'Collapsed', 'Auto'],
                  description: 'Scroll bar visibility.'
                },
alwaysShowScrollbar: { type: 'boolean', description: 'Always show scrollbar.' },
columnCount: { type: 'number', description: 'Number of columns.' },
rowCount: { type: 'number', description: 'Number of rows.' },
slotPadding: {
                  type: 'object',
                  properties: { left: commonSchemas.numberProp, top: commonSchemas.numberProp, right: commonSchemas.numberProp, bottom: commonSchemas.numberProp },
                  description: 'Padding between uniform grid slots.'
                },
minDesiredSlotWidth: { type: 'number', description: 'Minimum slot width.' },
minDesiredSlotHeight: { type: 'number', description: 'Minimum slot height.' },
innerSlotPadding: {
                  type: 'object',
                  properties: { left: commonSchemas.numberProp, top: commonSchemas.numberProp, right: commonSchemas.numberProp, bottom: commonSchemas.numberProp },
                  description: 'Inner wrap box slot padding.'
                },
wrapWidth: { type: 'number', description: 'Wrap width for wrap box.' },
explicitWrapWidth: { type: 'boolean', description: 'Use explicit wrap width.' },
widthOverride: { type: 'number', description: 'Width override for size box.' },
heightOverride: { type: 'number', description: 'Height override for size box.' },
minDesiredWidth: { type: 'number', description: 'Minimum desired width.' },
minDesiredHeight: { type: 'number', description: 'Minimum desired height.' },
stretch: {
                  type: 'string',
                  enum: ['None', 'Fill', 'ScaleToFit', 'ScaleToFitX', 'ScaleToFitY', 'ScaleToFill', 'UserSpecified'],
                  description: 'Scale box stretch mode.'
                },
stretchDirection: {
                  type: 'string',
                  enum: ['Both', 'DownOnly', 'UpOnly'],
                  description: 'Scale box stretch direction.'
                },
userSpecifiedScale: { type: 'number', description: 'User specified scale value.' },
brushColor: {
                  type: 'object',
                  properties: commonSchemas.colorObject.properties,
                  description: 'Border brush color.'
                },
padding: {
                  type: 'object',
                  properties: { left: commonSchemas.numberProp, top: commonSchemas.numberProp, right: commonSchemas.numberProp, bottom: commonSchemas.numberProp },
                  description: 'Widget slot padding.'
                },
bindingSource: { type: 'string', description: 'Variable or function name to bind to.' },
onHoveredFunction: { type: 'string', description: 'Function to call on hover.' },
onUnhoveredFunction: { type: 'string', description: 'Function to call on unhover.' },
animationName: commonSchemas.animationName,
trackType: {
                  type: 'string',
                  enum: ['transform', 'color', 'opacity', 'renderOpacity', 'material'],
                  description: 'Animation track type.'
                },
time: { type: 'number', description: 'Keyframe time.' },
interpolation: {
                  type: 'string',
                  enum: ['linear', 'cubic', 'constant'],
                  description: 'Keyframe interpolation.'
                },
loopCount: { type: 'number', description: 'Number of loops (-1 for infinite).' },
playMode: {
                  type: 'string',
                  enum: ['forward', 'reverse', 'pingpong'],
                  description: 'Animation play mode.'
                },
settingsType: {
                  type: 'string',
                  enum: ['video', 'audio', 'controls', 'gameplay', 'all'],
                  description: 'Settings menu type.'
                },
includeProgressBar: { type: 'boolean', description: 'Include progress bar.' },
promptFormat: { type: 'string', description: 'Interaction prompt format.' },
maxVisibleObjectives: { type: 'number', description: 'Maximum visible objectives.' },
fadeTime: commonSchemas.fadeTime,
gridSize: {
                  type: 'object',
                  properties: { columns: commonSchemas.numberProp, rows: commonSchemas.numberProp },
                  description: 'Inventory grid size.'
                },
showSpeakerName: { type: 'boolean', description: 'Show speaker name.' },
segmentCount: { type: 'number', description: 'Number of radial segments.' },
previewSize: {
                  type: 'string',
                  enum: ['1080p', '720p', 'mobile', 'custom'],
                  description: 'Preview resolution preset.'
                },
duration: commonSchemas.numberProp,
height: commonSchemas.numberProp,
nodeGuid: commonSchemas.stringProp,
nodeName: commonSchemas.nodeName,
parentName: commonSchemas.stringProp,
position: commonSchemas.location,
preset: commonSchemas.stringProp,
propertyValue: commonSchemas.value,
size: commonSchemas.numberProp,
sourceNode: commonSchemas.stringProp,
sourcePin: commonSchemas.sourcePin,
targetNode: commonSchemas.stringProp,
targetPin: commonSchemas.targetPin,
title: commonSchemas.stringProp,
width: commonSchemas.numberProp
};
