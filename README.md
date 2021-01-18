mycrowbot
------
mycrowbot is a Telegram bot to store, organize and access any media resource such as PDFs, e-books, videos, images. It is ideally made for a university network consisting of colleges, and their classes/courses/sections, managed by super admin(s), college admin(s) and class admin(s).

### Features

#### Student
<br/>
1. Access class resources through a menu-driven directory system.<br/>
2. Access class timetables/schedules for your college.<br/>
3. Track your attendance (if timetable is added by the admins).<br/>

#### Admin
|Type        | Access           |Permissions  |
| -------------|-------------| -----|
| Super Admin | Everything | <ul><li>Add/delete colleges, classes.</li><li>Assign college and class admins</li></ul> |
| College Admin | College | <ul><li>Manage resources, edit timetable for **all classes** at the college.</li><li>Assign class admins.</li><li>Accept/Decline join requests from Students.</li></ul>|
| Class Admin | Class | <ul><li>Manage resources, edit timetable for **the class**.</li><li>Transfer class admin role to somebody</li><ul> |
<br/>



### How does it work?
A student once registered(`/register`) at a class in a college can access the class's resources. The resources can be added and updated by the respective college and class admins.<br/>
Colleges can be openly accessible or restricted. For the latter, when a student joins, the college or class admin has the ability to accept or decline the Student's *Join Request* through the *Admin* menu (`/admin`).<br/>
College Admins can also control if students enrolled in class A can access resources of class B and C (`/admin`> Admin Menu > Select *Cross-Class Resources*).

###### The readme is still being updated with screenshots, command lists, etc.
