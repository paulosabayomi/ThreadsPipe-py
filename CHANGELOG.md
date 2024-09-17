# Changelog

## [Version 0.1.6] - 2024-09-18

### Fix

- Fixed a bug in pipe method in which the tags at the end posts that has newline or space characters are ignored

### Added

- Added `link_attachment_url` to the list of items to be returned for `get_post` abd `get_posts`.
- Added `threads_api_version` parameter, for changing/setting the Threads API version number, to the class object parameter and to the `update_param` method.

## [Version 0.1.5] - 2024-09-17

### Fix

- Fixed a bug in the `__split_post__` method causing the next batch of splitted posts, after adding hashtags, to reset back to the beginning.

## [Version 0.1.4] - 2024-09-17

### Added
  
- A test case for the supported file url formats
- Support for ip address file urls added
- Added support for ports in file urls

### Fix

- A fix for the RegExp check for file urls, the former RegExp doesn't pass for some urls and only matches some url formats and that caused errors which results into treating some file urls as local files.

## [Version 0.1.3] - 2024-09-17

### Fix

- A bug fix in the pipe method.

## [Version 0.1.2] - 2024-09-16

### Fix

- A bug fix in the pipe method.

## [Version 0.1.1] - 2024-09-16

### Fix

- A bug in the send_post method

## [Version 0.1.0] - 2024-09-16

### Added

- Added the `link_attachment` parameter to the `pipe` method for explicitly adding links to text-only posts
- Added response object to the ThreadsPipe response method `__tp_response_msg__`
