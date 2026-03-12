#!/usr/bin/env ruby
require 'fileutils'
require 'pathname'
require 'xcodeproj'

ROOT = Pathname.new(__dir__).join('..').realpath
APP_ROOT = ROOT.join('MLBShowDashboard')
PROJECT_PATH = ROOT.join('MLBShowDashboard.xcodeproj')

FileUtils.rm_rf(PROJECT_PATH)
project = Xcodeproj::Project.new(PROJECT_PATH.to_s)
project.root_object.attributes['LastUpgradeCheck'] = '2630'
project.root_object.attributes['TargetAttributes'] = {}

main_group = project.main_group
main_group.set_source_tree('<group>')
app_group = main_group.new_group('MLBShowDashboard', 'MLBShowDashboard')

app_target = project.new_target(:application, 'MLBShowDashboard', :ios, '17.0')
app_target.product_name = 'MLBShowDashboard'

project.build_configurations.each do |config|
  config.build_settings['SWIFT_VERSION'] = '5.0'
end

app_target.build_configurations.each do |config|
  settings = config.build_settings
  settings['PRODUCT_BUNDLE_IDENTIFIER'] = 'com.breezy.MLBShowDashboard'
  settings['MARKETING_VERSION'] = '1.0'
  settings['CURRENT_PROJECT_VERSION'] = '1'
  settings['SWIFT_VERSION'] = '5.0'
  settings['IPHONEOS_DEPLOYMENT_TARGET'] = '17.0'
  settings['TARGETED_DEVICE_FAMILY'] = '1'
  settings['SUPPORTED_PLATFORMS'] = 'iphonesimulator iphoneos'
  settings['CODE_SIGN_STYLE'] = 'Automatic'
  settings['GENERATE_INFOPLIST_FILE'] = 'YES'
  settings['INFOPLIST_KEY_CFBundleDisplayName'] = 'Show Intel'
  settings['INFOPLIST_KEY_UIUserInterfaceStyle'] = 'Dark'
  settings['INFOPLIST_KEY_UILaunchStoryboardName'] = 'LaunchScreen'
  settings['ASSETCATALOG_COMPILER_APPICON_NAME'] = 'AppIcon'
  settings['ASSETCATALOG_COMPILER_GLOBAL_ACCENT_COLOR_NAME'] = 'AccentColor'
  settings['OTHER_LDFLAGS'] = ['$(inherited)', '-ObjC']
  settings['ENABLE_PREVIEWS'] = 'YES'
end

def ensure_group(parent, relative_path)
  group = parent
  relative_path.each_filename do |component|
    next if component == '.'
    existing = group.groups.find { |child| child.display_name == component }
    group = existing || group.new_group(component, component)
  end
  group
end

def add_swift_files(project, target, app_group, app_root)
  Pathname.glob(app_root.join('**/*.swift')).sort.each do |file|
    relative = file.relative_path_from(app_root)
    group = ensure_group(app_group, relative.dirname)
    file_ref = group.new_file(file.basename.to_s)
    target.source_build_phase.add_file_reference(file_ref, true)
  end
end

def add_resource(project, target, app_group, app_root, relative_path)
  group = ensure_group(app_group, Pathname.new(relative_path).dirname)
  file_ref = group.new_file(Pathname.new(relative_path).basename.to_s)
  target.resources_build_phase.add_file_reference(file_ref, true)
end

add_swift_files(project, app_target, app_group, APP_ROOT)
add_resource(project, app_target, app_group, APP_ROOT, 'Resources/Assets.xcassets')
add_resource(project, app_target, app_group, APP_ROOT, 'Resources/LaunchScreen.storyboard')

project.save
puts "Generated #{PROJECT_PATH}"
